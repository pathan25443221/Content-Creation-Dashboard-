import os
import argparse
import sys
import subprocess
from datetime import datetime

def download_video(url: str, output_dir: str = "generator/raw") -> str:
    """
    Downloads a video from a given URL using yt-dlp.
    Returns the path to the downloaded MP4 file.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_template = os.path.join(output_dir, f"video_{timestamp}.%(ext)s")
    
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", out_template,
        url
    ]
    
    print(f"[Generator] Downloading video from {url}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Find the created file
        for file in os.listdir(output_dir):
            if file.startswith(f"video_{timestamp}") and file.endswith(".mp4"):
                downloaded_path = os.path.abspath(os.path.join(output_dir, file))
                print(f"[Generator] Successfully downloaded: {downloaded_path}")
                return downloaded_path
        
        # Fallback if extension differed
        files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.startswith(f"video_{timestamp}")]
        if files:
            print(f"[Generator] Successfully downloaded: {files[0]}")
            return os.path.abspath(files[0])
            
        raise RuntimeError("Downloaded file not found on disk.")
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
