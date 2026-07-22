# Architecture: Content Dashboard

## 1. App flow

The system runs as three independent stages that pass data forward. Each stage works standalone via its own CLI/entry point, and the dashboard sits on top reading from the shared database.

```
                 ┌─────────────────────────────────────────┐
                 │  1. GENERATION                           │
                 │  video URL/file → vertical short clips   │
                 └─────────────────────────────────────────┘
   URL/file ──▶  download.py ──▶ router.py
                                    │
                     ┌──────────────┴───────────────┐
                     ▼                               ▼
              speech_based/                    visual_based/
              transcribe → diarize             audio_energy
              → select_clips (LLM)             + motion_detect
                     │                          → select_clips
                     └──────────────┬───────────────┘
                                    ▼
                              render.py (cut, 9:16, captions)
                                    │
                                    ▼
                         generator/output/*.mp4
                                    │
                                    ▼
                 ┌─────────────────────────────────────────┐
                 │  2. PUBLISHING                           │
                 │  clip → reviewed → posted to platforms   │
                 └─────────────────────────────────────────┘
                    review/approve queue (operator)
                                    │
                          queue.py (rate-limit safe)
                          ┌─────────┴─────────┐
                          ▼                   ▼
                 youtube_upload.py    instagram_upload.py
                          │                   │
                          └─────────┬─────────┘
                                    ▼
                          db.posts (platform, post_id, posted_at)

                 ┌─────────────────────────────────────────┐
                 │  3. ANALYTICS                            │
                 │  poll platforms → store metrics → view   │
                 └─────────────────────────────────────────┘
              scheduler.py (polls every N hours)
                          │
              ┌───────────┴────────────┐
              ▼                        ▼
     fetch_youtube_stats.py   fetch_instagram_insights.py
              │                        │
              └───────────┬────────────┘
                           ▼
                  db.metrics (views, likes,
                    comments, reach, timestamp)
                           │
                           ▼
              dashboard (backend API + frontend UI)
```

**End-to-end path for one video:** URL in → downloaded → routed to speech or visual path → candidate clips selected → rendered as vertical mp4s → operator reviews/approves in the dashboard → queued and posted to YouTube/Instagram → metrics polled on a schedule → visible in the dashboard.

## 2. Architecture principles

- **Stage independence**: `generator/`, `publisher/`, and `analytics/` each work as standalone CLI tools before being wired together. This keeps debugging isolated to one stage at a time.
- **Shared data contract, not shared code**: the speech and visual clip-selection paths both output the same shape (`start`, `end`, `reason`) so `render.py` and everything downstream doesn't need to know which path a clip came from.
- **Human-in-the-loop by default**: nothing posts without operator approval in v1. Automation can be added later once clip-selection quality is trusted.
- **Local-first AI**: transcription, clip selection, and vision tagging run on local models (Whisper, Ollama) rather than paid cloud APIs, per the free/open-source constraint in the PRD.
- **Single source of truth for data**: one database holds videos, posts, and metrics; the dashboard is a read layer on top of it, not a separate data store.

## 3. Folder and file structure

```
content-dashboard/
├── README.md
├── PRD.md
├── ARCHITECTURE.md
├── .env.example                   # API keys, never commit the real .env
├── docker-compose.yml             # postgres + app, all local
│
├── generator/                     # STAGE 1 — video in, short out
│   ├── download.py                # yt-dlp wrapper: url -> raw mp4
│   ├── router.py                  # decides speech_based vs visual_based per video
│   ├── speech_based/              # talking-head, podcasts, tutorials, narrated vlogs
│   │   ├── transcribe.py          # local Whisper -> transcript.json
│   │   ├── diarize.py             # pyannote.audio -> who said what (multi-speaker)
│   │   └── select_clips.py        # local LLM (Ollama) reasons over transcript text
│   ├── visual_based/              # football, gameplay, silent/no-dialogue video
│   │   ├── audio_energy.py        # librosa -> flag volume spikes
│   │   ├── motion_detect.py       # PySceneDetect/frame-diff -> flag high visual change
│   │   ├── vision_tag.py          # LLaVA/Moondream via Ollama -> tag sampled frames
│   │   └── select_clips.py        # combines the 3 signals into candidate timestamps
│   ├── render.py                  # ffmpeg: crop 9:16, burn captions (shared by both paths)
│   ├── models/                    # whisper/vision model files (gitignored)
│   └── output/                    # generated .mp4 shorts land here
│
├── publisher/                     # STAGE 2 — short out, post to platforms
│   ├── youtube_upload.py
│   ├── instagram_upload.py
│   ├── queue.py                   # job queue, rate-limit aware
│   └── credentials/               # OAuth tokens per platform (gitignored)
│
├── analytics/                     # STAGE 3 — pull metrics back
│   ├── fetch_youtube_stats.py
│   ├── fetch_instagram_insights.py
│   ├── scheduler.py               # cron-like: poll every N hours
│   └── db/
│       ├── schema.sql
│       └── models.py
│
├── dashboard/                     # web UI, reads from the shared db
│   ├── backend/                   # FastAPI, serves /videos, /posts, /metrics
│   │   └── main.py
│   └── frontend/                  # React or plain HTML + Chart.js
│       └── src/
│
└── scripts/
    ├── setup_local_llm.sh         # pulls Ollama model
    └── init_db.sh
```

## 4. Data model (high level)

```
videos     : id, source_url, downloaded_at, type (speech|visual)
clips      : id, video_id, start_time, end_time, reason, file_path
posts      : id, clip_id, platform, platform_post_id, posted_at, status
metrics    : id, post_id, fetched_at, views, likes, comments, reach
```

`clips` are generated in Stage 1, become `posts` once approved and published in Stage 2, and accumulate `metrics` rows over time in Stage 3.

## 5. Tech stack

| Layer | Tool | Why |
|---|---|---|
| Video download | yt-dlp | Free, actively maintained, handles YouTube URLs |
| Video/audio processing | ffmpeg | Industry-standard, free, handles cropping/cutting/captions |
| Transcription | faster-whisper (local) | Free, runs on CPU, no per-minute API cost |
| Speaker diarization | pyannote.audio | Free, handles multi-speaker transcripts |
| Clip selection (speech) | Ollama + local LLM (e.g. Llama 3.1 8B) | Free, no API cost, runs locally |
| Audio energy detection | librosa | Free, lightweight signal-processing library |
| Motion/scene detection | PySceneDetect | Free, purpose-built for scene-change detection |
| Vision tagging (optional) | LLaVA / Moondream via Ollama | Free, local, for non-speech frame analysis |
| Publishing | YouTube Data API, Instagram Graph API | Official, free-tier APIs |
| Database | SQLite (dev) / Postgres (production-ish) | Free, simple, easy to self-host |
| Backend | FastAPI (Python) | Lightweight, fast to build, same language as the rest of the pipeline |
| Frontend | React or plain HTML + Chart.js | Free, simple charting for the dashboard views |
| Job queue | Custom, backed by a SQLite/Postgres table | No need for a heavier queue system (Redis/Celery) at this scale |
| Hosting | Local machine or free-tier VPS | Keeps the whole system cost-free per the PRD constraint |

## 6. What's intentionally NOT in this architecture (v1)

- No message broker/queue system (Redis, RabbitMQ) — a database-backed queue table is enough at personal-project scale.
- No multi-tenant auth system — single operator, no user accounts.
- No paid cloud AI APIs — all AI steps are local-first per the PRD's free/open-source constraint.
- No support for platforms beyond YouTube and Instagram — kept out of scope to match the PRD.
