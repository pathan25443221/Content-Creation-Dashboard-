import os
import sys
import json
import argparse
import subprocess

def generate_srt_subtitles(transcript_json_path: str, start: float, end: float, srt_out_path: str) -> bool:
    """Generates an SRT subtitle file for segments within [start, end]."""
    if not transcript_json_path or not os.path.exists(transcript_json_path):
        return False
        
    try:
        with open(transcript_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        segments = data.get("segments", [])
        clip_segments = []
        
        for seg in segments:
            s_start = seg["start"]
            s_end = seg["end"]
            if s_end > start and s_start < end:
                rel_start = max(0.0, s_start - start)
                rel_end = min(end - start, s_end - start)
                if rel_end > rel_start:
                    clip_segments.append({
                        "start": rel_start,
                        "end": rel_end,
                        "text": seg["text"].strip()
                    })

        if not clip_segments:
            return False

        def format_timestamp(seconds: float) -> str:
            millis = int((seconds % 1) * 1000)
            secs = int(seconds)
            mins = secs // 60
            hours = mins // 60
            mins = mins % 60
            secs = secs % 60
            return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

        with open(srt_out_path, "w", encoding="utf-8") as f:
            for idx, seg in enumerate(clip_segments, start=1):
                f.write(f"{idx}\n")
                f.write(f"{format_timestamp(seg['start'])} --> {format_timestamp(seg['end'])}\n")
                f.write(f"{seg['text']}\n\n")

        return True
    except Exception as e:
        print(f"[Warning] Failed to generate SRT subtitles: {e}", file=sys.stderr)
        return False

def render_clip(video_path: str, start: float, end: float, output_path: str, transcript_json_path: str = None, x_ratio: float = 0.5, y_ratio: float = 0.5, layout_mode: str = "visual_split") -> str:
    """
    Renders a vertical 9:16 clip from raw video between start and end timestamps using ffmpeg.
    If layout_mode is visual_split, uses a split-screen layout (gameplay top, face bottom).
    Otherwise, uses a standard 9:16 full-height crop tracking the face or centered.
    Burns subtitles if transcript JSON is provided.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    duration = end - start

    if layout_mode == "visual_split":
        # Split screen complex filter
        # Top crop (Gameplay - center of original video)
        top_crop = "crop=ih*(9/16):ih/2:(iw-ih*(9/16))/2:(ih-ih/2)/2"
        
        # Bottom crop (Face Cam)
        # FFmpeg requires commas inside functions to be escaped with \
        face_x = f"max(0\\,min(iw-ih*(9/16)\\,iw*{x_ratio}-ih*(9/16)/2))"
        face_y = f"max(0\\,min(ih-ih/2\\,ih*{y_ratio}-ih/4))"
        bottom_crop = f"crop=ih*(9/16):ih/2:{face_x}:{face_y}"
        
        # Combine using vstack
        filter_complex = f"[0:v]{top_crop}[top];[0:v]{bottom_crop}[bottom];[top][bottom]vstack=inputs=2[stacked]"
    else:
        # Standard 9:16 crop (Full height)
        # Tracks x_ratio, but full height (so y is always 0)
        face_x = f"max(0\\,min(iw-ih*(9/16)\\,iw*{x_ratio}-ih*(9/16)/2))"
        filter_complex = f"[0:v]crop=ih*(9/16):ih:{face_x}:0[stacked]"

    # Burn captions if transcript is present
    if transcript_json_path:
        srt_path = output_path.replace(".mp4", ".srt")
        has_srt = generate_srt_subtitles(transcript_json_path, start, end, srt_path)
        if has_srt:
            escaped_srt = srt_path.replace("\\", "/").replace(":", "\\:")
            # Overlay subtitles on the [stacked] stream
            filter_complex += f",[stacked]subtitles='{escaped_srt}':force_style='Fontname=Arial,Fontsize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Alignment=2'[outv]"
        else:
            filter_complex += ";[stacked]copy[outv]"
    else:
        filter_complex += ";[stacked]copy[outv]"

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", video_path,
        "-t", str(duration),
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "0:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path
    ]

    print(f"[Render] Rendering split-screen clip ({start}s -> {end}s): {output_path}...")
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"[Render] Completed: {output_path}")
        return os.path.abspath(output_path)
    except subprocess.CalledProcessError as e:
        print(f"[Error] ffmpeg rendering failed: {e.stderr}", file=sys.stderr)
        raise e

def render_clips_from_list(video_path: str, clips: list, output_dir: str = "generator/output", transcript_json_path: str = None, layout_mode: str = "visual_split") -> list:
    """
    Renders multiple candidate clips from a list.
    Returns list of rendered clip file details.
    """
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(video_path))[0]

    # Import face tracking here to avoid circular imports if any, and only load OpenCV when needed
    try:
        from generator.visual_based.face_tracking import get_focal_point_ratios
    except ImportError:
        def get_focal_point_ratios(v, s, e): return (0.5, 0.5)

    rendered_clips = []
    for idx, clip in enumerate(clips, start=1):
        start = clip["start"]
        end = clip["end"]
        reason = clip.get("reason", "Clip selection")
        title = clip.get("title", f"Short {idx}")
        
        out_filename = f"{base_name}_short_{idx}.mp4"
        out_path = os.path.join(output_dir, out_filename)

        # Get face coordinates dynamically
        x_ratio, y_ratio = get_focal_point_ratios(video_path, start, end)

        rendered_path = render_clip(
            video_path, start, end, out_path, 
            transcript_json_path=transcript_json_path,
            x_ratio=x_ratio, y_ratio=y_ratio,
            layout_mode=layout_mode
        )
        
        rendered_clips.append({
            "clip_number": idx,
            "start": start,
            "end": end,
            "reason": reason,
            "title": title,
            "virality_score": clip.get("virality_score", round(9.5 - idx * 0.4, 1)),
            "file_path": rendered_path
        })

    return rendered_clips

def main():
    parser = argparse.ArgumentParser(description="Render candidate 9:16 vertical short clips using ffmpeg.")
    parser.add_argument("video_path", help="Path to raw mp4 file")
    parser.add_argument("clips_json", help="Path to clips JSON array or JSON string")
    parser.add_argument("--output-dir", default="generator/output", help="Output directory for rendered clips")

    args = parser.parse_args()
    try:
        if os.path.exists(args.clips_json):
            with open(args.clips_json, "r", encoding="utf-8") as f:
                clips = json.load(f)
        else:
            clips = json.loads(args.clips_json)

        rendered = render_clips_from_list(args.video_path, clips, args.output_dir)
        print(json.dumps(rendered, indent=2))
    except Exception as e:
        print(f"[Error] Render process failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
