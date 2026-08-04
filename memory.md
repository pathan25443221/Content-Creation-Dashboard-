# Project Memory & Progress Log

## Project Summary
The **Content Creation Dashboard** is an autonomous, single-operator short-form video generation, publishing, and analytics platform. It automatically processes long-form videos (or YouTube URLs), transcribes audio with Whisper, selects top candidate clip segments using local LLMs (Ollama `llama3.1:8b`), renders vertical 9:16 shorts with burned-in captions via `ffmpeg`, and allows one-click approval to publish across YouTube Shorts and Instagram Reels with automated metrics collection.

---

## 1. System Architecture & Components Completed

### Phase 0: Environment & Central Configuration
- **Central Configuration ([config.py](file:///d:/Personal%20Projects/content%20DashBoard/Content-Creation-Dashboard-/config.py))**: Environment settings loaded once via `pydantic-settings` / `python-dotenv`. All modules load settings strictly through `config.py`.
- **Environment Verification ([scripts/check_env.py](file:///d:/Personal%20Projects/content%20DashBoard/Content-Creation-Dashboard-/scripts/check_env.py))**: Automated verifier checking `ffmpeg`, `yt-dlp`, `Python 3.14+`, and active `Ollama` service status.
- **Git Security ([.gitignore](file:///d:/Personal%20Projects/content%20DashBoard/Content-Creation-Dashboard-/.gitignore))**: Strictly excludes `.env`, `*.db`, `publisher/credentials/*`, `generator/raw/*`, `generator/output/*`, and `node_modules/`.

### Stage 1: Content Generation Pipeline
- **Downloader ([generator/download.py](file:///d:/Personal%20Projects/content%20DashBoard/Content-Creation-Dashboard-/generator/download.py))**: `yt-dlp` wrapper for YouTube URLs and local video files.
- **Speech Path - Transcription ([generator/speech_based/transcribe.py](file:///d:/Personal%20Projects/content%20DashBoard/Content-Creation-Dashboard-/generator/speech_based/transcribe.py))**: Local speech-to-text using `faster-whisper` (int8 quantized).
- **Speech Path - Clip Selection ([generator/speech_based/select_clips.py](file:///d:/Personal%20Projects/content%20DashBoard/Content-Creation-Dashboard-/generator/speech_based/select_clips.py))**: 
  - Enforces `format="json"` via `Ollama` (`llama3.1:8b`) for structured clip selection.
  - Sentence-aligned fallback selector ensuring clips never cut in the middle of spoken sentences.
- **Visual Path - Spikes & Cuts ([generator/visual_based/audio_energy.py](file:///d:/Personal%20Projects/content%20DashBoard/Content-Creation-Dashboard-/generator/visual_based/audio_energy.py), [generator/visual_based/motion_detect.py](file:///d:/Personal%20Projects/content%20DashBoard/Content-Creation-Dashboard-/generator/visual_based/motion_detect.py))**: `librosa` audio volume spike detection and `PySceneDetect` motion scene cuts.
- **Vertical Renderer & Subtitle Burner ([generator/render.py](file:///d:/Personal%20Projects/content%20DashBoard/Content-Creation-Dashboard-/generator/render.py))**:
  - Crops 16:9 video to 9:16 vertical ratio (`crop=ih*(9/16):ih`).
  - Automatically extracts timestamped transcript segments, generates `.srt` subtitle files, and burns centered high-contrast captions into vertical short videos.
- **Orchestrator Router ([generator/router.py](file:///d:/Personal%20Projects/content%20DashBoard/Content-Creation-Dashboard-/generator/router.py))**: Pipeline entrypoint routing speech/visual paths and registering clips in database.

### Database & Models
- **Database Schema ([analytics/db/models.py](file:///d:/Personal%20Projects/content%20DashBoard/Content-Creation-Dashboard-/analytics/db/models.py))**: SQLModel definitions for `Video`, `Clip`, `Post`, and `Metric`.
- **Database Initializer ([scripts/init_db.py](file:///d:/Personal%20Projects/content%20DashBoard/Content-Creation-Dashboard-/scripts/init_db.py))**: Table creation & migration script (`content_dashboard.db`).

### Stage 2 & 3: Publishing & Analytics Engine
- **Queue Manager ([publisher/queue.py](file:///d:/Personal%20Projects/content%20DashBoard/Content-Creation-Dashboard-/publisher/queue.py))**: Manages job state for pending/approved/published clips.
- **YouTube Shorts Uploader ([publisher/youtube_upload.py](file:///d:/Personal%20Projects/content%20DashBoard/Content-Creation-Dashboard-/publisher/youtube_upload.py))**: YouTube Data API v3 uploader with automatic stub fallback when credentials are missing.
- **Instagram Reels Uploader ([publisher/instagram_upload.py](file:///d:/Personal%20Projects/content%20DashBoard/Content-Creation-Dashboard-/publisher/instagram_upload.py))**: Instagram Graph API 2-step container uploader with automatic stub fallback.
- **Analytics Fetchers & Scheduler ([analytics/fetch_youtube_stats.py](file:///d:/Personal%20Projects/content%20DashBoard/Content-Creation-Dashboard-/analytics/fetch_youtube_stats.py), [analytics/fetch_instagram_insights.py](file:///d:/Personal%20Projects/content%20DashBoard/Content-Creation-Dashboard-/analytics/fetch_instagram_insights.py), [analytics/scheduler.py](file:///d:/Personal%20Projects/content%20DashBoard/Content-Creation-Dashboard-/analytics/scheduler.py))**: Background polling scheduler capturing Views, Likes, Comments, and Shares.

### Single-Operator Web Console
- **FastAPI Backend ([dashboard/backend/main.py](file:///d:/Personal%20Projects/content%20DashBoard/Content-Creation-Dashboard-/dashboard/backend/main.py))**:
  - Non-blocking async background processing (`BackgroundTasks`) for video generation to avoid HTTP timeouts.
  - Mounts `/api/media` static server for streaming generated MP4 short clips.
- **React + Vite Frontend ([dashboard/frontend/src/App.jsx](file:///d:/Personal%20Projects/content%20DashBoard/Content-Creation-Dashboard-/dashboard/frontend/src/App.jsx))**:
  - Dark-mode dashboard UI with Overview, Generate Shorts, Review Queue, Published Posts, and Analytics.
  - HTML5 video player embedded in Review Queue for clip approval and caption editing.
  - Auto-polling background status updater.

---

## 2. Currently Being Worked On / Next Steps

- [x] Enforce `format="json"` in Ollama clip selection (`select_clips.py`).
- [x] Prevent mid-sentence video cuts via sentence-aligned timestamp boundaries.
- [x] Burn centered subtitles directly onto rendered 9:16 vertical video clips via `ffmpeg`.
- [x] Support advanced subtitle animations (TikTok Pop, Fade In) by dynamically rendering `.ass` files.
- [x] Add embedded HTML5 video player in Review Queue (`App.jsx` + FastAPI `/api/media` static mount).
- [x] Extract YouTube metadata & tags (`generator/download.py`) for dynamic genre-adaptive LLM hook prompting (`select_clips.py`).
- [x] Fast-path pre-existing YouTube captions (`.vtt`/`.srt` in `transcribe.py`) to bypass Whisper CPU transcription.
- [x] Automatic local disk cleanup of rejected `.mp4`/`.ass` files and raw source videos (`main.py` & `router.py`).
- [x] Vizard.ai style 2-column Review Queue cards with virality scores (`9.2 VIRALITY`), short titles, viral reason callout boxes, and timestamped spoken subtitle previews.
- [x] Dynamic AI reasoning quoting exact spoken lines/concepts from transcript without generic template text.
- [x] Guarantee 3 distinct 20–50 second candidate clips per video pipeline run.
- [x] Multimodal Scoring Engine: Combines LLM `hook_strength` with physical `librosa` Audio Energy and `PySceneDetect` Visual Pace.
- [x] Dense context chunking for LLM prompt to prevent slicing jokes/stories during downsampling.
- [ ] Connect real Instagram API credentials when available.
- [x] Implement proper Google OAuth token caching for YouTube uploads to prevent repeated logins.
- [x] Implement custom video cropping focal point (face/speaker tracking with split-screen layout).
- [x] Implemented dynamic face tracking for the bottom face-cam in `visual_split` layout, replacing the static average crop.
- [x] Completely modularized FastAPI backend into `routers/` and `services/` enforcing strict DRY principles.
- [x] Implemented Hybrid Multimodal Clipping for `visual_split` (Audio Energy Spikes + Whisper Transcript boundary snapping).
- [x] Added dynamic LLM enhancement for visual clip Titles & Descriptions based on video metadata and exact spoken transcript snippets.
- [x] Built robust JSON dictionary extraction fallback for Ollama to handle varying LLM output payloads safely.
- [x] Optimized `visual_split` render layout to 65% top (gameplay) and 35% bottom (facecam) for an improved widescreen-friendly aesthetic.
- [x] Implemented robust UI local file bypass parsing in `download.py` to accept Windows "Copy as path" paths directly.
- [x] Fixed PySceneDetect FFmpeg proxy generation crash by downgrading strict `-hwaccel cuda` to `auto`, massively accelerating analysis times.
- [x] Redesigned Review Queue UI to dynamically inject hashtags directly into the video Title instead of a separate input field.
- [x] Enhanced visual clip fallback logic to use original video filenames instead of generic titles when local AI JSON generation fails or times out.
- [x] Fixed `sqlite3.ProgrammingError` by properly casting generated hashtag lists to comma-separated strings before SQL insertion.
- [x] Triggered foreground local server login flow to cache fresh YouTube OAuth tokens with full `youtube.readonly` scopes, fixing Analytics 403 errors.

---

## 3. Key Command Reference

- **Check System Dependencies**: `python scripts/check_env.py`
- **Initialize Database**: `python scripts/init_db.py`
- **Start FastAPI Backend**: `$env:PYTHONPATH="."; python -m uvicorn dashboard.backend.main:app --port 8000 --reload`
- **Start Vite Frontend**: `cd dashboard/frontend && npm run dev`
- **Run Generation via CLI**: `python generator/router.py "https://youtu.be/..." --type speech`
