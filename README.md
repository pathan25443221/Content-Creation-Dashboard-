# Content Dashboard

Turn a long-form video into short-form clips, post them across your social accounts, and track how each one performs — all in one place, built on free and open-source tools.

## What it does

- **Generate** — feed it a video URL (or file) and it produces short, vertical clips ready for Reels/Shorts/TikTok-style feeds.
  - Talking-head, podcast, and tutorial content: transcribed locally (Whisper) and reasoned over by a local LLM (Ollama) to find self-contained hooks, punchlines, and key points.
  - Non-speech content (sports footage, gameplay, silent video): clips are surfaced using audio energy spikes and visual motion detection instead of a transcript.
- **Publish** — posts the generated clips to your connected social accounts (currently YouTube and Instagram) through their official APIs, with a review/approve step before anything goes live.
- **Track** — pulls back likes, views, reach, and comments for every posted clip on a schedule, and surfaces them in a simple dashboard so performance is visible in one place instead of spread across apps.

## Why

Repurposing long-form content into shorts is valuable but tedious to do by hand, and most tools that automate it are paid SaaS products. This project does the same job using self-hosted, open-source pieces — no subscription, no vendor lock-in, runs on your own machine.

## Status

Early / in development. Built incrementally, module by module — generation, publishing, and analytics each work as standalone pieces before being wired together end to end.

## Stack

- **Video/audio**: yt-dlp, ffmpeg, faster-whisper, librosa, PySceneDetect
- **Local AI**: Ollama (LLM for clip selection, optional vision model for non-speech content)
- **Publishing**: YouTube Data API, Instagram Graph API
- **Backend/data**: Python, SQLite/Postgres, FastAPI
- **Frontend**: simple web dashboard (React or HTML + Chart.js)

## Disclaimer

Auto-posting repurposed content, especially footage you don't own (broadcasts, licensed game footage, etc.), can raise copyright/ToS considerations independent of this tool. Use it responsibly with content you have the rights to repurpose.

## License

MIT (or your preferred license)
