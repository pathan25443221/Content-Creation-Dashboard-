import os
import sys
from typing import List, Optional
from sqlmodel import Session, select, func
from config import settings
from analytics.db.models import Video, Clip, Post
from publisher.queue import queue_clip_for_publishing, process_publishing_queue

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

def list_clips(session: Session, status: Optional[str] = None):
    query = select(Clip)
    if status:
        query = query.where(Clip.status == status)
    query = query.order_by(Clip.created_at.desc())
    clips = session.exec(query).all()

    result = []
    for c in clips:
        video = session.get(Video, c.video_id)
        posts = session.exec(select(Post).where(Post.clip_id == c.id)).all()
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
            "description": c.description or "",
            "hashtags": c.hashtags or "",
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

def approve_clip(session: Session, clip_id: int, req_title: Optional[str], req_desc: Optional[str], req_hashtags: Optional[str], platforms: List[str]):
    clip = session.get(Clip, clip_id)
    if not clip:
        return False, "Clip not found."

    if req_title:
        clip.title = req_title
    if req_desc is not None:
        clip.description = req_desc
    if req_hashtags is not None:
        clip.hashtags = req_hashtags
        
    clip.status = "approved"
    session.add(clip)
    session.commit()

    queue_clip_for_publishing(clip_id, platforms)
    process_publishing_queue()
    return True, f"Clip {clip_id} approved and queued for publishing."

def reject_clip(session: Session, clip_id: int):
    clip = session.get(Clip, clip_id)
    if not clip:
        return False, "Clip not found."
    
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

    return True, f"Clip {clip_id} rejected and files cleaned up."
