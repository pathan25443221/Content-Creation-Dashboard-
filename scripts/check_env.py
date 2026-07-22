import shutil
import sys
import subprocess
import os

def check_command(cmd, name):
    path = shutil.which(cmd)
    if path:
        print(f"[OK] {name} is installed at: {path}")
        return True
    else:
        print(f"[MISSING] {name} ('{cmd}') was not found in PATH.")
        return False

def check_python_version():
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print(f"[OK] Python version: {sys.version.split()[0]}")
        return True
    else:
        print(f"[WARNING] Python version {sys.version.split()[0]} detected. Python 3.10+ is recommended.")
        return False

def check_ollama_service():
    if not shutil.which("ollama"):
        print("[MISSING] Ollama CLI not found.")
        return False
    try:
        import requests
        res = requests.get("http://localhost:11434/api/tags", timeout=3)
        if res.status_code == 200:
            models = [m.get("name") for m in res.json().get("models", [])]
            print(f"[OK] Ollama service is running. Available models: {models}")
            return True
        else:
            print("[WARNING] Ollama service responded with non-200 status.")
            return False
    except Exception:
        print("[WARNING] Ollama CLI exists, but local service is not responding at http://localhost:11434.")
        print("         Make sure to run 'ollama serve' or start the Ollama desktop app.")
        return False

def main():
    print("=" * 50)
    print(" Content Dashboard — Environment & Dependency Check")
    print("=" * 50)
    
    python_ok = check_python_version()
    ffmpeg_ok = check_command("ffmpeg", "ffmpeg (Video Processing)")
    ytdlp_ok = check_command("yt-dlp", "yt-dlp (Video Downloading)")
    ollama_ok = check_command("ollama", "Ollama (Local LLM Server)")
    
    if ollama_ok:
        check_ollama_service()
        
    print("-" * 50)
    if python_ok and ffmpeg_ok and ytdlp_ok:
        print("Result: Core environment tools ready.")
    else:
        print("Result: Some required tools are missing. Please install them to proceed with Phase 1 & 2.")

if __name__ == "__main__":
    main()
