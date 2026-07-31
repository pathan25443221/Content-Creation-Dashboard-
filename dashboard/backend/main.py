import os
import sys
from typing import Optional, List
from datetime import datetime, timedelta
import asyncio
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, create_engine, select, func
from config import settings

from analytics.db.models import Video, Clip, Post, Metric
from generator.router import process_video_pipeline
from publisher.queue import queue_clip_for_publishing, process_publishing_queue
from analytics.scheduler import poll_all_post_metrics

engine = create_engine(settings.DATABASE_URL, echo=False)

app = FastAPI(
    title="Content Dashboard API",
    description="Backend API serving the single-operator content generation, review, publishing, and analytics dashboard.",
    version="1.0.0"
)

# SSE Global State
connected_clients = set()
main_loop = None

@app.on_event("startup")
async def startup_event():
    global main_loop
    main_loop = asyncio.get_running_loop()

def notify_clients(event_data: str):
    """Safely notifies all connected SSE clients from sync or async contexts."""
    if not main_loop:
        return
    for q in list(connected_clients):
        main_loop.call_soon_threadsafe(q.put_nowait, event_data)

# Enable CORS for React frontend (Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated media short files
os.makedirs("generator/output", exist_ok=True)
app.mount("/api/media", StaticFiles(directory="generator/output"), name="media")

@app.get("/")
def health_check():
    """API Root Health Check endpoint."""
    return {
        "status": "ok",
        "message": "Content Dashboard API is up and running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/stream")
async def sse_stream(request: Request):
    """Server-Sent Events endpoint for real-time UI updates."""
    async def event_generator():
        q = asyncio.Queue()
        connected_clients.add(q)
        try:
            while True:
                if await request.is_disconnected():
                    break
                data = await q.get()
                yield f"data: {data}\n\n"
        finally:
            connected_clients.remove(q)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Pydantic Request Models
class GenerateRequest(BaseModel):
    video_input: str
    video_type: str = "speech"
    burn_captions: bool = True
    quantity: int = 3
    quality: str = "high"
    caption_color: str = "white"
    caption_animation: str = "none"

class ApproveRequest(BaseModel):
    title: Optional[str] = None
    platforms: List[str] = ["youtube", "instagram"]

@app.get("/api/overview")
def get_overview():
    """Summary metrics for the Home/Overview screen."""
    with Session(engine) as session:
        total_clips = session.exec(select(func.count(Clip.id))).one()
        pending_review_count = session.exec(
            select(func.count(Clip.id)).where(Clip.status == "pending")
        ).one()

        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_posts_count = session.exec(
            select(func.count(Post.id)).where(Post.posted_at >= seven_days_ago)
        ).one()

        metrics_sum = session.exec(
            select(func.sum(Metric.views), func.sum(Metric.likes))
        ).one()

        total_views = metrics_sum[0] or 0
        total_likes = metrics_sum[1] or 0

        # Recent activities
        recent_clips = session.exec(
            select(Clip).order_by(Clip.created_at.desc()).limit(5)
        ).all()

        return {
            "total_clips": total_clips,
            "pending_review_count": pending_review_count,
            "recent_posts_count": recent_posts_count,
            "total_views": total_views,
            "total_likes": total_likes,
            "recent_activity": [
                {
                    "id": c.id,
                    "title": c.title or f"Clip #{c.id}",
                    "status": c.status,
                    "created_at": c.created_at.isoformat()
                }
                for c in recent_clips
            ]
        }

def get_clip_transcript_lines(file_path: str, start_time: float, end_time: float) -> list:
    """Reads SRT or VTT file matching clip file_path to provide timestamped transcript lines."""
    lines = []
    target_path = file_path.replace(".mp4", ".srt")
    if not os.path.exists(target_path):
        target_path = file_path.replace(".mp4", ".vtt")
        if not os.path.exists(target_path):
            return []
            
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            content = f.read().split("\n\n")
            for block in content:
                pts = block.split("\n")
                if len(pts) >= 3:
                    ts_line = pts[1]
                    text = " ".join(pts[2:])
                    start_str = ts_line.split("-->")[0].strip()
                    ts_clean = start_str.split(",")[0].split(".")[0]
                    colons = ts_clean.split(":")
                    if len(colons) == 3:
                        ts_clean = f"{colons[1]}:{colons[2]}"
                    if text and not text.startswith("WEBVTT"):
                        lines.append({"timestamp": ts_clean, "text": text})
    except Exception as e:
        print(f"[Warning] Failed to read transcript lines from {target_path}: {e}")
    return lines[:6]

@app.get("/api/clips")
def list_clips(status: Optional[str] = None):
    """Fetch clips with optional status filter ('pending', 'approved', 'rejected')."""
    with Session(engine) as session:
        query = select(Clip)
        if status:
            query = query.where(Clip.status == status)
        query = query.order_by(Clip.created_at.desc())
        clips = session.exec(query).all()

        result = []
        for c in clips:
            video = session.get(Video, c.video_id)
            posts = session.exec(select(Post).where(Post.clip_id == c.id)).all()
            
            # Extract transcript lines for Vizard UI
            t_lines = get_clip_transcript_lines(c.file_path, c.start_time, c.end_time)

            result.append({
                "id": c.id,
                "video_id": c.video_id,
                "video_title": video.title if video else "Unknown Video",
                "start_time": c.start_time,
                "end_time": c.end_time,
                "duration": round(c.end_time - c.start_time, 2),
                "reason": c.reason,
                "file_path": c.file_path,
                "media_url": f"/api/media/{os.path.basename(c.file_path)}",
                "title": c.title or f"Clip #{c.id}",
                "virality_score": round(getattr(c, "virality_score", 8.5) or 8.5, 1),
                "transcript_lines": t_lines,
                "status": c.status,
                "created_at": c.created_at.isoformat(),
                "posts": [
                    {
                        "id": p.id,
                        "platform": p.platform,
                        "status": p.status,
                        "platform_post_id": p.platform_post_id,
                        "posted_at": p.posted_at.isoformat() if p.posted_at else None
                    }
                    for p in posts
                ]
            })
        return result

def run_pipeline_task(video_input: str, video_type: str, burn_captions: bool, quantity: int, quality: str, caption_color: str, caption_animation: str):
    try:
        process_video_pipeline(
            video_input, video_type, burn_captions=burn_captions, 
            quantity=quantity, quality=quality,
            caption_color=caption_color, caption_animation=caption_animation,
            progress_callback=lambda msg: notify_clients(f"progress:{msg}")
        )
        notify_clients("update")
        notify_clients("progress:done")
    except Exception as e:
        print(f"[Error] Background generation pipeline failed: {e}", file=sys.stderr)
        notify_clients(f"progress:Error: {str(e)}")

@app.post("/api/generate", status_code=202)
def trigger_generation(req: GenerateRequest, background_tasks: BackgroundTasks):
    """Triggers Stage 1 video generation pipeline in the background."""
    background_tasks.add_task(
        run_pipeline_task, 
        req.video_input, 
        req.video_type, 
        req.burn_captions,
        req.quantity,
        req.quality,
        req.caption_color,
        req.caption_animation
    )
    return {
        "message": "Generation pipeline started in background. Downloading & transcribing...",
        "status": "processing"
    }

@app.post("/api/clips/{clip_id}/approve")
def approve_clip(clip_id: int, req: ApproveRequest):
    """Approves a clip from the review queue and enqueues it for publishing."""
    with Session(engine) as session:
        clip = session.get(Clip, clip_id)
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found.")

        if req.title:
            clip.title = req.title
        clip.status = "approved"
        session.add(clip)
        session.commit()

    queued_posts = queue_clip_for_publishing(clip_id, req.platforms)
    
    # Process queue synchronously or via worker
    process_publishing_queue()
    notify_clients("update")

    return {
        "message": f"Clip {clip_id} approved and queued for publishing.",
        "queued_platforms": req.platforms
    }

@app.post("/api/clips/{clip_id}/reject")
def reject_clip(clip_id: int):
    """Rejects a clip from the review queue and deletes its rendered media files from disk."""
    with Session(engine) as session:
        clip = session.get(Clip, clip_id)
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found.")
        
        # Delete rendered MP4 & SRT from generator/output
        if clip.file_path and os.path.exists(clip.file_path):
            try:
                os.remove(clip.file_path)
                print(f"[Cleanup] Deleted rejected clip file: {clip.file_path}")
            except Exception as e:
                print(f"[Warning] Failed to delete clip file {clip.file_path}: {e}", file=sys.stderr)

            srt_path = clip.file_path.replace(".mp4", ".srt")
            if os.path.exists(srt_path):
                try:
                    os.remove(srt_path)
                    print(f"[Cleanup] Deleted subtitle file: {srt_path}")
                except Exception as e:
                    print(f"[Warning] Failed to delete subtitle file {srt_path}: {e}", file=sys.stderr)

        clip.status = "rejected"
        session.add(clip)
        session.commit()

        # Check if all clips for this video are no longer pending -> cleanup raw video file
        video = session.get(Video, clip.video_id)
        if video and video.local_path:
            pending_count = session.exec(
                select(func.count(Clip.id)).where(Clip.video_id == video.id, Clip.status == "pending")
            ).one()
            if pending_count == 0 and os.path.exists(video.local_path):
                try:
                    os.remove(video.local_path)
                    print(f"[Cleanup] Deleted raw source video file: {video.local_path}")
                except Exception as e:
                    print(f"[Warning] Failed to delete raw video file {video.local_path}: {e}", file=sys.stderr)

    notify_clients("update")
    return {"message": f"Clip {clip_id} rejected and files cleaned up."}

@app.get("/api/posts")
def list_posts():
    """Returns library of all published and queued posts."""
    with Session(engine) as session:
        posts = session.exec(select(Post).order_by(Post.id.desc())).all()
        result = []
        for p in posts:
            clip = session.get(Clip, p.clip_id)
            metrics = session.exec(
                select(Metric).where(Metric.post_id == p.id).order_by(Metric.fetched_at.desc())
            ).first()

            result.append({
                "id": p.id,
                "clip_id": p.clip_id,
                "clip_title": clip.title if clip else "Clip",
                "platform": p.platform,
                "platform_post_id": p.platform_post_id,
                "posted_at": p.posted_at.isoformat() if p.posted_at else None,
                "status": p.status,
                "error_message": p.error_message,
                "latest_metrics": {
                    "views": metrics.views if metrics else 0,
                    "likes": metrics.likes if metrics else 0,
                    "comments": metrics.comments if metrics else 0,
                    "reach": metrics.reach if metrics else None
                } if metrics else None
            })
        return result

@app.post("/api/analytics/poll")
def trigger_metrics_poll():
    """Polls latest analytics from connected social platforms."""
    poll_all_post_metrics()
    return {"message": "Metrics poll triggered successfully."}
