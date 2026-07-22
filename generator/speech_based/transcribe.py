import os
import sys
import json
import argparse

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from faster_whisper import WhisperModel

def transcribe_audio(video_path: str, model_size: str = "tiny", device: str = "cpu") -> str:
    """
    Transcribes audio from a video file using faster-whisper locally.
    Outputs a timestamped JSON file.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found at: {video_path}")

    print(f"[Transcribe] Loading Whisper model ('{model_size}' on {device})...")
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
