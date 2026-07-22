import os
import sys
import json
import argparse

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import re

def parse_time_str(t_str: str) -> float:
    """Parses HH:MM:SS.mmm or MM:SS.mmm to seconds float."""
    t_str = t_str.replace(',', '.')
    parts = t_str.strip().split(':')
    if len(parts) == 3:
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return float(parts[0]) * 60 + float(parts[1])
    return float(parts[0])

def parse_subtitles_to_transcript_json(sub_path: str, video_path: str) -> str:
    """Fast-path parser for existing YouTube VTT/SRT captions."""
    print(f"[Transcribe] FAST-PATH: Reading pre-existing YouTube captions from {sub_path}...")
    with open(sub_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Regex for subtitle timestamp blocks
    timestamp_pattern = re.compile(r"(\d{1,2}:?\d{2}:\d{2}[\.,]\d{3})\s*-->\s*(\d{1,2}:?\d{2}:\d{2}[\.,]\d{3})")
    lines = content.split('\n')
    
    segments = []
    curr_start, curr_end, curr_text = None, None, []
    
    for line in lines:
        line_s = line.strip()
        match = timestamp_pattern.search(line_s)
        if match:
            if curr_start is not None and curr_text:
                txt = " ".join(curr_text).strip()
                # Clean VTT formatting tags like <c> or 00:00:00.000
                txt = re.sub(r'<[^>]+>', '', txt)
                if txt:
                    segments.append({
                        "id": len(segments),
                        "start": round(curr_start, 2),
                        "end": round(curr_end, 2),
                        "text": txt
                    })
            curr_start = parse_time_str(match.group(1))
            curr_end = parse_time_str(match.group(2))
            curr_text = []
        elif line_s and not line_s.isdigit() and "WEBVTT" not in line_s and "Kind:" not in line_s and "Language:" not in line_s:
            curr_text.append(line_s)

    if curr_start is not None and curr_text:
        txt = " ".join(curr_text).strip()
        txt = re.sub(r'<[^>]+>', '', txt)
        if txt:
            segments.append({
                "id": len(segments),
                "start": round(curr_start, 2),
                "end": round(curr_end, 2),
                "text": txt
            })

    total_duration = segments[-1]["end"] if segments else 60.0
    full_text = " ".join([s["text"] for s in segments])

    result = {
        "video_path": os.path.abspath(video_path),
        "language": "en",
        "duration": round(total_duration, 2),
        "full_text": full_text,
        "segments": segments
    }

    base_name = os.path.splitext(video_path)[0]
    output_json_path = f"{base_name}_transcript.json"
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"[Transcribe] FAST-PATH Complete! Saved transcript with {len(segments)} segments to: {output_json_path}")
    return os.path.abspath(output_json_path)

def transcribe_audio(video_path: str, model_size: str = "tiny", device: str = "cpu", sub_path: str = None) -> str:
    """
    Transcribes audio from a video file using pre-existing subtitles if available,
    or falls back to faster-whisper locally.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found at: {video_path}")

    # 1. Fast-Path: Use YouTube subtitles if available
    if sub_path and os.path.exists(sub_path):
        try:
            return parse_subtitles_to_transcript_json(sub_path, video_path)
        except Exception as e:
            print(f"[Warning] Subtitle fast-path failed ({e}). Falling back to local Whisper...", file=sys.stderr)

    # 2. Local Whisper Fallback
    print(f"[Transcribe] Loading Whisper model ('{model_size}' on {device})...")
    from faster_whisper import WhisperModel
    model = WhisperModel(model_size, device=device, compute_type="int8")

    print(f"[Transcribe] Transcribing video: {video_path}...")
    segments, info = model.transcribe(video_path, beam_size=5)

    transcript_segments = []
    full_text = []

    for segment in segments:
        segment_data = {
            "id": segment.id,
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip()
        }
        transcript_segments.append(segment_data)
        full_text.append(segment.text.strip())

    result = {
        "video_path": os.path.abspath(video_path),
        "language": info.language,
        "duration": round(info.duration, 2),
        "full_text": " ".join(full_text),
        "segments": transcript_segments
    }

    base_name = os.path.splitext(os.path.basename(video_path))[0]
    output_json = os.path.abspath(os.path.join(os.path.dirname(video_path), f"{base_name}_transcript.json"))

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"[Transcribe] Transcript saved to: {output_json}")
    return output_json

def main():
    parser = argparse.ArgumentParser(description="Transcribe video audio using faster-whisper.")
    parser.add_argument("video_path", help="Path to raw mp4 file")
    parser.add_argument("--model-size", default="tiny", help="Whisper model size (tiny, base, small, medium)")
    parser.add_argument("--device", default="cpu", help="Device to run inference on (cpu, cuda)")

    args = parser.parse_args()
    try:
        json_path = transcribe_audio(args.video_path, args.model_size, args.device)
        print(f"TRANSCRIPT_JSON={json_path}")
    except Exception as e:
        print(f"[Error] Transcription failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
