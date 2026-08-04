import os
import argparse
import sys
import json
import time
import uuid
import re
import yt_dlp

def download_video(url: str, output_dir: str = "generator/raw", quality: str = "high") -> dict:
    """
    Downloads a video from a given URL using yt-dlp native Python API, OR accepts a local file path.
    Extracts video metadata (title, tags, category) and downloads YouTube subtitles if available.
    Returns dict containing video_path, sub_path (if any), and metadata.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    unique_prefix = f"vid_{uuid.uuid4().hex[:8]}"
    out_template = os.path.join(output_dir, f"{unique_prefix}.%(ext)s")

    # Strip surrounding quotes (common when using "Copy as path" in Windows)
    clean_url = url.strip('"\' ')

    # [LOCAL FILE BYPASS] - If the 'url' is actually a local file on the computer, skip downloading!
    if os.path.exists(clean_url) and os.path.isfile(clean_url):
        print(f"[Generator] Using LOCAL FILE bypass for: {clean_url}")
        import shutil
        ext = os.path.splitext(clean_url)[1] or ".mp4"
        local_video_path = os.path.join(output_dir, f"{unique_prefix}{ext}")
        shutil.copy2(clean_url, local_video_path)
        
        return {
            "video_path": local_video_path,
            "sub_path": None,
            "metadata": {
                "title": os.path.basename(clean_url),
                "tags": ["Local", "Video"],
                "category": "Local File"
            }
        }
    
    # Select download format based on requested quality to save bandwidth.
    # We remove the H.264 restriction so it can grab 4K (AV1/VP9) streams if available.
    format_str = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    if quality == "medium":
        format_str = 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]/best'
    elif quality == "low":
        format_str = 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best'

    import shutil
    # Hardcode path because Uvicorn process might not have ffmpeg in PATH
    ffmpeg_path = r"C:\ffmpeg-8.0-essentials_build\bin\ffmpeg.exe"

    ydl_opts = {
        'format': format_str,
        'merge_output_format': 'mp4',
        'outtmpl': out_template,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['hi.*', 'en.*', 'hi', 'en'],
        'subtitlesformat': 'vtt/srt',
        'writeinfojson': True,
        'ignoreerrors': True,
        'quiet': False,
        'no_warnings': True,
        'ffmpeg_location': ffmpeg_path
    }
    
    # If the user provided a cookies.txt file (exported from Zen browser), use it
    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = "cookies.txt"
    
    print(f"[Generator] Downloading video & metadata from {url}... (ffmpeg={ffmpeg_path})")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        video_path = None
        info_json_path = None
        sub_path = None
        
        for file in os.listdir(output_dir):
            full_p = os.path.abspath(os.path.join(output_dir, file))
            if file.startswith(unique_prefix):
                if file.endswith(".info.json"):
                    info_json_path = full_p
                elif file.endswith((".vtt", ".srt")):
                    if not sub_path or file.endswith(".srt"):
                        sub_path = full_p
                elif file.endswith((".mp4", ".webm", ".mkv", ".mov", ".avi")) and not file.endswith(".part"):
                    if not re.search(r'\.f\d+\.', file):
                        video_path = full_p

        # Fallback: check most recent media file in last 120s
        if not video_path:
            recent_files = []
            now = time.time()
            for file in os.listdir(output_dir):
                full_p = os.path.abspath(os.path.join(output_dir, file))
                if file.endswith((".mp4", ".webm", ".mkv", ".mov", ".avi")) and not file.endswith(".part"):
                    if not re.search(r'\.f\d+\.', file) and (now - os.path.getmtime(full_p)) <= 120:
                        recent_files.append((os.path.getmtime(full_p), full_p))
            if recent_files:
                recent_files.sort(reverse=True)
                video_path = recent_files[0][1]

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
        safe_title = metadata['title'].encode('ascii', 'ignore').decode()
        print(f"[Generator] Metadata extracted: Title='{safe_title}', Tags={metadata['tags'][:5]}")

        return {
            "video_path": video_path,
            "info_json_path": info_json_path,
            "sub_path": sub_path,
            "metadata": metadata
        }
    except Exception as e:
        print(f"[Error] yt-dlp download failed: {str(e)}", file=sys.stderr)
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
