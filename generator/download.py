import os
import argparse
import sys
import subprocess
from datetime import datetime

def download_video(url: str, output_dir: str = "generator/raw") -> dict:
    """
    Downloads a video from a given URL using yt-dlp.
    Extracts video metadata (title, tags, category) and downloads YouTube subtitles if available.
    Returns dict containing video_path, sub_path (if any), and metadata.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_template = os.path.join(output_dir, f"video_{timestamp}.%(ext)s")
    
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "--write-info-json",
        "--write-sub",
        "--write-auto-sub",
        "--sub-lang", "en,hi,es",
        "--sub-format", "vtt/srt",
        "-o", out_template,
        url
    ]
    
    print(f"[Generator] Downloading video & metadata from {url}...")
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        video_path = None
        info_json_path = None
        sub_path = None
        
        for file in os.listdir(output_dir):
            full_p = os.path.abspath(os.path.join(output_dir, file))
            if file.startswith(f"video_{timestamp}"):
                if file.endswith(".mp4"):
                    video_path = full_p
                elif file.endswith(".info.json"):
                    info_json_path = full_p
                elif file.endswith(".vtt") or file.endswith(".srt"):
                    if not sub_path or file.endswith(".srt"):  # Prefer srt over vtt if both exist
                        sub_path = full_p

        if not video_path:
            # Fallback search
            for file in os.listdir(output_dir):
                if file.startswith(f"video_{timestamp}") and not file.endswith(".json") and not file.endswith(".vtt") and not file.endswith(".srt"):
                    video_path = os.path.abspath(os.path.join(output_dir, file))
                    break

        if not video_path:
            raise RuntimeError("Downloaded video file not found on disk.")

        # Read metadata if info.json exists
        metadata = {"title": os.path.basename(video_path), "tags": [], "category": "General", "description": ""}
        if info_json_path and os.path.exists(info_json_path):
            try:
                import json
                with open(info_json_path, "r", encoding="utf-8") as f:
                    info_data = json.load(f)
                    metadata["title"] = info_data.get("title") or metadata["title"]
                    metadata["tags"] = info_data.get("tags") or []
                    metadata["categories"] = info_data.get("categories") or []
                    metadata["description"] = info_data.get("description") or ""
            except Exception as e:
                print(f"[Warning] Failed to parse info json metadata: {e}", file=sys.stderr)

        print(f"[Generator] Download completed: {video_path}")
        if sub_path:
            print(f"[Generator] Subtitles downloaded: {sub_path}")
        print(f"[Generator] Metadata extracted: Title='{metadata['title']}', Tags={metadata['tags'][:5]}")

        return {
            "video_path": video_path,
            "info_json_path": info_json_path,
            "sub_path": sub_path,
            "metadata": metadata
        }
    except subprocess.CalledProcessError as e:
        print(f"[Error] yt-dlp download failed: {e.stderr}", file=sys.stderr)
        raise e

def main():
    parser = argparse.ArgumentParser(description="Download long-form video via yt-dlp.")
    parser.add_argument("url", help="YouTube video URL or supported media URL")
    parser.add_argument("--output-dir", default="generator/raw", help="Directory to save downloaded raw video")
    
    args = parser.parse_args()
    try:
        video_path = download_video(args.url, args.output_dir)
        print(f"OUTPUT_PATH={video_path}")
    except Exception as e:
        print(f"[Error] Download process failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
