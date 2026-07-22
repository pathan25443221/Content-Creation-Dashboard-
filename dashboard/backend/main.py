import os
import sys
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
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

# Pydantic Request Models
class GenerateRequest(BaseModel):
    video_input: str
    video_type: str = "speech"  # "speech" or "visual"

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
                "title": c.title,
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

def run_pipeline_task(video_input: str, video_type: str):
    try:
        process_video_pipeline(video_input, video_type)
    except Exception as e:
        print(f"[Error] Background generation pipeline failed: {e}", file=sys.stderr)

@app.post("/api/generate", status_code=202)
def trigger_generation(req: GenerateRequest, background_tasks: BackgroundTasks):
    """Triggers Stage 1 video generation pipeline in the background."""
    background_tasks.add_task(run_pipeline_task, req.video_input, req.video_type)
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

    return {
        "message": f"Clip {clip_id} approved and queued for publishing.",
        "queued_platforms": req.platforms
    }

@app.post("/api/clips/{clip_id}/reject")
def reject_clip(clip_id: int):
    """Rejects a clip from the review queue."""
    with Session(engine) as session:
        clip = session.get(Clip, clip_id)
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found.")
        clip.status = "rejected"
        session.add(clip)
        session.commit()
    return {"message": f"Clip {clip_id} rejected."}

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
