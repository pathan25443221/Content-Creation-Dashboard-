# Content Creation Dashboard

An autonomous, single-operator short-form video generation, publishing, and analytics platform. Turn a long-form video into short-form clips, post them across your social accounts, and track how each one performs — all in one place, built on free and open-source tools.

## Features

- **Generate** — feed it a video URL (or file) and it produces short, vertical clips ready for Reels/Shorts/TikTok-style feeds.
  - **Speech-Based Content** (Talking-head, podcast, tutorials): Transcribed locally using Whisper and reasoned over by a local LLM (`llama3.1:8b`) to find self-contained hooks, punchlines, and key points. Subtitles are dynamically burned into the final 9:16 video.
  - **Visual-Based Content** (Gaming, sports, silent video): Clips are surfaced using physical audio energy spikes (`librosa`) and visual motion cut detection (`PySceneDetect`). Enhanced with AI-generated titles and descriptions (`llama3.2:3b`).
- **Review & Publish** — An integrated React UI allows you to review candidate clips, edit titles/descriptions, and one-click publish to YouTube Shorts and Instagram Reels.
- **Track** — A background scheduler continuously polls YouTube/Instagram APIs to fetch views, likes, and comments, surfacing them on your dashboard.

---

## 🛠 Prerequisites

Before starting, ensure you have the following installed on your system:

1. **Python 3.10+** (Tested on Python 3.14)
2. **Node.js 18+** & `npm` (For the frontend)
3. **FFmpeg** 
   - Download FFmpeg and place the `ffmpeg.exe` binary in your system. 
   - *Note: Some python scripts in this repo (`generator/download.py`, `generator/render.py`, `generator/visual_based/motion_detect.py`) currently have a hardcoded FFmpeg path (`C:\ffmpeg-8.0-essentials_build\bin\ffmpeg.exe`). You will need to either place FFmpeg there OR update those 3 files to match your local FFmpeg path.*
4. **Ollama** (Local AI Engine)
   - Download and install [Ollama](https://ollama.com/).
   - Pull the required models by running:
     ```bash
     ollama run llama3.1:8b
     ollama run llama3.2:3b
     ```

---

## 🚀 Setup Instructions

### 1. Clone & Python Environment
```bash
git clone <your-repo-url>
cd Content-Creation-Dashboard-

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration & Database
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Initialize the SQLite Database:
   ```bash
   python scripts/init_db.py
   ```

### 3. Setup YouTube OAuth (Required for Publishing & Analytics)
1. Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a project.
2. Enable the **YouTube Data API v3**.
3. Create an **OAuth 2.0 Client ID** (Desktop App).
4. Download the JSON credentials and save them as:
   `publisher/credentials/youtube_client_secret.json`
5. To generate your session token (`youtube_token.json`), run the analytics script manually once. This will pop open a browser window asking you to log in with your Google Account:
   ```bash
   python -c "from google_auth_oauthlib.flow import InstalledAppFlow; creds = InstalledAppFlow.from_client_secrets_file('publisher/credentials/youtube_client_secret.json', ['https://www.googleapis.com/auth/youtube']).run_local_server(port=0); open('publisher/credentials/youtube_token.json', 'w').write(creds.to_json())"
   ```

### 4. Running the Application

You need to run both the FastAPI backend and the React frontend simultaneously.

**Terminal 1 (Backend):**
```bash
# Ensure you are in the root directory and your venv is activated
$env:PYTHONPATH="."  # On Windows PowerShell to ensure modules resolve correctly
python -m uvicorn dashboard.backend.main:app --port 8000 --reload
```

**Terminal 2 (Frontend):**
```bash
cd dashboard/frontend
npm install
npm run dev
```

Your dashboard will now be live at `http://localhost:5173`!

---

## 💡 Usage Tips
- **Downloading Restricted Videos**: If a YouTube video is age-restricted or requires login, use a browser extension to export your cookies to a `cookies.txt` file and place it in the root directory of this project. `yt-dlp` will automatically use it.
- **Local Files**: You can bypass the YouTube downloader entirely by pasting the absolute local file path of an `.mp4` video directly into the dashboard's generator input.
- **Hardware Acceleration**: The `PySceneDetect` proxy generation is configured to use `-hwaccel auto` to utilize NVIDIA/Intel GPUs when available for faster processing.

---

## License
MIT License
