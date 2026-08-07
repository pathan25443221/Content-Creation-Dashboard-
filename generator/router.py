import os
import sys
import json
import argparse
from datetime import datetime
from sqlmodel import Session, create_engine, select
from config import settings

# Import pipeline tools
from generator.download import download_video
from generator.speech_based.transcribe import transcribe_audio
from generator.speech_based.select_clips import select_clips as select_speech_clips
from generator.render import render_clips_from_list
from analytics.db.models import Video, Clip

engine = create_engine(settings.DATABASE_URL, echo=False)

def process_video_pipeline(video_input: str, video_type: str = "speech", ollama_model: str = "llama3.2:3b", burn_captions: bool = True, quantity: int = 3, quality: str = "high", caption_color: str = "white", caption_animation: str = "none", progress_callback=None) -> dict:
    """
    End-to-end stage 1 pipeline:
    1. If input is a URL, download video. If local file, use directly.
    2. Transcribe (speech path) or analyze audio/motion (visual path).
    3. Select candidate clips.
    4. Render 9:16 vertical mp4 shorts.
    5. Record video and clips in the SQLite database.
    """
    # Strip surrounding quotes (common when using "Copy as path" in Windows)
    video_input = video_input.strip('"\' ')
    
    print(f"[Router] Starting generation pipeline for: {video_input} (type={video_type}, burn_captions={burn_captions}, quantity={quantity}, quality={quality})")
    
    # 1. Download or locate video file
    raw_video_path = None
    sub_path = None
    metadata = {}
    if progress_callback: progress_callback("Initializing...")
    
    if video_input.startswith("http://") or video_input.startswith("https://"):
        if progress_callback: progress_callback("Downloading video (this might take a bit depending on quality)...")
        dl_res = download_video(video_input, quality=quality)
        raw_video_path = dl_res["video_path"]
        sub_path = dl_res.get("sub_path")
        metadata = dl_res.get("metadata", {})
    else:
        raw_video_path = os.path.abspath(video_input)
        metadata = {"title": os.path.basename(raw_video_path), "tags": [], "categories": []}

    if not os.path.exists(raw_video_path):
        raise FileNotFoundError(f"Raw video path does not exist: {raw_video_path}")

    # 2. Select candidates based on path
    transcript_json = None
    if video_type in ["speech", "vlog", "center"]:
        print(f"[Router] Path: Speech-based content (mode: {video_type})")
        if progress_callback: progress_callback("Transcribing audio (AI listening)...")
        transcript_json = transcribe_audio(raw_video_path, model_size="tiny", sub_path=sub_path)
        if progress_callback: progress_callback("AI is reading transcript to find the best viral hooks...")
        candidate_clips = select_speech_clips(transcript_json, model_name=ollama_model, metadata=metadata, raw_video_path=raw_video_path, quantity=quantity)
    elif video_type in ["visual", "visual_split"]:
        print("[Router] Path: Visual-based content (Multimodal)")
        if progress_callback: progress_callback("Transcribing audio for multimodal analysis...")
        transcript_json = transcribe_audio(raw_video_path, model_size="tiny", sub_path=sub_path)
        if progress_callback: progress_callback("Scanning video for action and motion spikes...")
        from generator.visual_based.select_clips import select_visual_clips
        candidate_clips = select_visual_clips(raw_video_path, target_count=quantity, metadata=metadata, transcript_json=transcript_json)
    else:
        raise ValueError(f"Unsupported video_type: {video_type}")

    # Truncate candidates to user-requested quantity
    if len(candidate_clips) > quantity:
        print(f"[Router] Truncating candidate clips from {len(candidate_clips)} to requested quantity {quantity}.")
        candidate_clips = candidate_clips[:quantity]

    # 3. Render 9:16 vertical clips
    print(f"[Router] Rendering {len(candidate_clips)} candidate clips (Captions: {'ON' if burn_captions else 'OFF'}, Quality: {quality})...")
    if progress_callback: progress_callback(f"Rendering {len(candidate_clips)} perfect short clips...")
    render_transcript = transcript_json if burn_captions else None
    rendered_clips = render_clips_from_list(
        raw_video_path, 
        candidate_clips, 
        transcript_json_path=render_transcript, 
        layout_mode=video_type,
        quality=quality,
        caption_color=caption_color,
        caption_animation=caption_animation
    )

    # 4. Save to Database
    if progress_callback: progress_callback("Saving everything to database...")
    video_title = metadata.get("title") or os.path.basename(raw_video_path)
    with Session(engine) as session:
        video_entry = Video(
            source_url=video_input,
            video_type=video_type,
            local_path=raw_video_path,
            title=video_title
        )
        session.add(video_entry)
        session.commit()
        session.refresh(video_entry)

        db_clips = []
        for c in rendered_clips:
            clip_entry = Clip(
                video_id=video_entry.id,
                start_time=c["start"],
                end_time=c["end"],
                reason=c["reason"],
                file_path=c["file_path"],
                title=c.get("title", f"Highlight #{int(c['start'])}"),
                description=c.get("description"),
                hashtags=", ".join(c.get("hashtags", [])) if isinstance(c.get("hashtags"), list) else c.get("hashtags"),
                virality_score=c.get("virality_score", 8.5),
                status="pending"
            )
            session.add(clip_entry)
            db_clips.append(clip_entry)
        
        video_id = video_entry.id
        session.commit()
        for dc in db_clips:
            session.refresh(dc)

    # 5. Cleanup raw/temporary files
    print("[Router] Cleaning up temporary raw files...")
    if video_input.startswith("http://") or video_input.startswith("https://"):
        try:
            if raw_video_path and os.path.exists(raw_video_path):
                os.remove(raw_video_path)
            if 'dl_res' in locals() and dl_res:
                info_p = dl_res.get("info_json_path")
                if info_p and os.path.exists(info_p):
                    os.remove(info_p)
                sub_p = dl_res.get("sub_path")
                if sub_p and os.path.exists(sub_p):
                    os.remove(sub_p)
        except Exception as e:
            print(f"[Warning] Failed to cleanup raw video files: {e}", file=sys.stderr)
            
    if transcript_json and os.path.exists(transcript_json):
        try:
            os.remove(transcript_json)
        except Exception as e:
            print(f"[Warning] Failed to cleanup transcript json: {e}", file=sys.stderr)

    result = {
        "video_id": video_id,
        "raw_video_path": raw_video_path,
        "video_type": video_type,
        "clips_generated": len(rendered_clips),
        "clips": rendered_clips
    }
    return result

def main():
    parser = argparse.ArgumentParser(description="ClipForge Generator Router.")
    parser.add_argument("video_input", help="Video URL or local mp4 file path")
    parser.add_argument("--type", choices=["speech", "visual"], default="speech", help="Path type")
    parser.add_argument("--model", default="llama3.1:8b", help="Ollama model for clip selection")

    args = parser.parse_args()
    try:
        res = process_video_pipeline(args.video_input, args.type, args.model)
        print("=" * 50)
        print(" GENERATION COMPLETED SUCCESSFULLY")
        print("=" * 50)
        print(json.dumps(res, indent=2))
    except Exception as e:
        print(f"[Error] Generation pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
