import sys
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlmodel import Session, create_engine
from config import settings

from dashboard.backend.schemas.requests import GenerateRequest, ApproveRequest
from dashboard.backend.services.clip_service import list_clips, approve_clip, reject_clip
from dashboard.backend.core.sse import notify_clients
from generator.router import process_video_pipeline

engine = create_engine(settings.DATABASE_URL, echo=False)
router = APIRouter()

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

@router.get("/clips")
def get_clips(status: Optional[str] = None):
    """Fetch clips with optional status filter."""
    with Session(engine) as session:
        return list_clips(session, status)

@router.post("/generate", status_code=202)
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

@router.post("/clips/{clip_id}/approve")
def api_approve_clip(clip_id: int, req: ApproveRequest):
    """Approves a clip from the review queue and enqueues it for publishing."""
    with Session(engine) as session:
        success, message = approve_clip(session, clip_id, req.title, req.description, req.hashtags, req.platforms)
        if not success:
            raise HTTPException(status_code=404, detail=message)
    
    notify_clients("update")
    return {
        "message": message,
        "queued_platforms": req.platforms
    }

@router.post("/clips/{clip_id}/reject")
def api_reject_clip(clip_id: int):
    """Rejects a clip from the review queue and deletes its rendered media files from disk."""
    with Session(engine) as session:
        success, message = reject_clip(session, clip_id)
        if not success:
            raise HTTPException(status_code=404, detail=message)
            
    notify_clients("update")
    return {"message": message}
