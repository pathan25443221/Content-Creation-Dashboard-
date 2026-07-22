# Content Dashboard — Build Plan

A free/open-source pipeline: YouTube video → auto-generated shorts → auto-post to socials → analytics dashboard.

Built in 3 stages, each one working end-to-end before you touch the next.

---

## Folder structure

```
content-dashboard/
├── README.md
├── .env.example                  # API keys, never commit the real .env
├── docker-compose.yml            # postgres + redis + app, all local
│
├── generator/                    # STAGE 1 — video in, short out
│   ├── download.py               # yt-dlp wrapper: url -> raw mp4
│   ├── router.py                 # decides speech_based vs visual_based per video
│   ├── speech_based/             # talking-head, podcasts, tutorials, vlogs w/ narration
│   │   ├── transcribe.py         # local Whisper -> transcript.json
│   │   ├── diarize.py            # pyannote.audio -> who said what (multi-speaker)
│   │   └── select_clips.py       # local LLM (Ollama) reasons over transcript text
│   ├── visual_based/              # football, gameplay (GTA 6 etc.), silent/no-dialogue video
│   │   ├── audio_energy.py       # librosa -> flag volume spikes (crowd roar, explosions)
│   │   ├── motion_detect.py      # PySceneDetect/frame-diff -> flag high visual change
│   │   ├── vision_tag.py         # LLaVA/Moondream via Ollama -> tag sampled frames
│   │   └── select_clips.py       # combines the 3 signals above into candidate timestamps
│   ├── render.py                 # ffmpeg: crop 9:16, burn captions (shared by both paths)
│   ├── models/                   # whisper/vision model files (gitignored)
│   └── output/                   # generated .mp4 shorts land here
│
├── publisher/                    # STAGE 2 — short out, post to platforms
│   ├── youtube_upload.py
│   ├── instagram_upload.py
│   ├── queue.py                  # job queue so you don't blow rate limits
│   └── credentials/               # OAuth tokens per platform (gitignored)
│
├── analytics/                    # STAGE 3 — pull metrics back
│   ├── fetch_youtube_stats.py
│   ├── fetch_instagram_insights.py
│   ├── scheduler.py              # cron-like: poll every N hours
│   └── db/
│       ├── schema.sql
│       └── models.py
│
├── dashboard/                    # web UI
│   ├── backend/                  # FastAPI or Flask, serves data from db
│   │   └── main.py
│   └── frontend/                 # React or plain HTML+Chart.js
│       └── src/
│
└── scripts/
    ├── setup_local_llm.sh        # pulls Ollama model
    └── init_db.sh
```

Keep `generator/`, `publisher/`, and `analytics/` as **independent modules** with their own CLI entry points (`python download.py <url>`). Don't couple them until each works standalone — you'll debug 10x faster.

---

## Week-by-week plan

### Week 1 — Generator, part 1: get a raw video in + the speech path
- Install `yt-dlp`, `ffmpeg`, Python env.
- `download.py`: paste a YouTube URL, get an mp4 on disk.
- `router.py`: for now, just a manual flag (`--type speech` or `--type visual`) — auto-detection can come later.
- Install local Whisper (`faster-whisper`). `speech_based/transcribe.py`: mp4 → timestamped transcript JSON.
- **Done when:** you can run `python download.py <url>` then `python speech_based/transcribe.py video.mp4` and get a clean transcript file, for a talking-head style video.

### Week 2 — Generator, part 2: speech-based clip selection
- Install Ollama, pull a small local model (Llama 3.1 8B or similar).
- `speech_based/select_clips.py`: feed the transcript to the local model, prompt it to return 2–4 candidate clip timestamps with a one-line reason each (hook, punchline, self-contained point). Parse as JSON.
- If your source has multiple speakers (interviews, panels), add `speech_based/diarize.py` (pyannote.audio) so the LLM knows who said what.
- `render.py`: use ffmpeg to cut those timestamp ranges, crop to 9:16, burn in captions from the transcript.
- **Done when:** one command chain takes a talking-head YouTube URL and produces 2–4 finished vertical mp4s in `generator/output/`.

### Week 3 — Generator, part 3: visual-based path (football, gameplay, silent video)
- `visual_based/audio_energy.py`: use librosa to flag timestamps where volume spikes well above the rolling average (crowd roar, explosions, big hits).
- `visual_based/motion_detect.py`: use PySceneDetect or simple frame-differencing to flag high visual-change moments.
- `visual_based/select_clips.py`: combine both signals — a timestamp both flag is a strong candidate. Feed the same output shape (`start`, `end`, `reason`) that `render.py` already expects from the speech path, so `render.py` doesn't need to change.
- Optional stretch: `visual_based/vision_tag.py` using a local vision model (LLaVA/Moondream via Ollama) on sampled frames, for a third confirming signal.
- **Done when:** you can run this path on a football clip or gameplay footage and get 2–4 candidate vertical shorts, same as the speech path does for talking-head video.

### Week 4 — Publisher, part 1: YouTube (easiest platform first)
- Set up a Google Cloud project, enable YouTube Data API, get OAuth credentials.
- `youtube_upload.py`: upload one generated short, set title/description (from the transcript if speech-based, or a generic template if visual-based).
- Watch your quota (10,000 units/day, ~1,600 per upload — plenty for a personal channel).
- **Done when:** a generated short lands on your YouTube channel as a Short via script, not manual upload.

### Week 5 — Publisher, part 2: Instagram
- Convert your Instagram account to Business or Creator and link it to a Facebook Page (required — personal accounts can't use the API).
- Create a Meta developer app, request the content-publish permission (expect a review wait, roughly 1–2 weeks — start this early).
- `instagram_upload.py`: two-step container flow (create container → publish). Respect the 100 posts/24h cap and the 90-second Reels window.
- **Done when:** a short posts to Instagram Reels via script. (If review is still pending, move to Week 6 and come back.)

### Week 6 — Publisher, part 3: the job queue
- Build `queue.py`: a simple job queue (even just a SQLite table with status columns is fine) so uploads across platforms don't fire all at once and hit rate limits.
- Add retry/backoff logic for both YouTube and Instagram uploads.
- **Done when:** one script call queues a short for both platforms and posts them with appropriate spacing.

### Week 7 — Analytics, part 1: pull the numbers back
- Design `schema.sql`: tables for `videos`, `posts` (platform, post_id, posted_at), `metrics` (post_id, timestamp, views, likes, comments, reach).
- Write `fetch_youtube_stats.py` and `fetch_instagram_insights.py` (Instagram insights need >1,000 followers on the account to return data — check this before assuming it'll work on a new account).
- `scheduler.py`: poll each platform every few hours, insert new metric rows.
- **Done when:** metrics for your posted shorts are accumulating in your local database automatically.

### Week 8 — Dashboard backend + frontend
- FastAPI backend exposing `/videos`, `/posts`, `/metrics` reading from the same database.
- Frontend: a simple table/grid of shorts with per-platform like/view/reach numbers, plus one chart (e.g. views over time per short) using Chart.js or Recharts.
- **Done when:** you can open a local webpage and see every short you've generated, where it's posted, and how it's performing — no manual checking of each app.

### Week 9 — Glue, polish, and guardrails
- Connect the three stages: a single "generate → review → approve → publish" flow in the UI, so nothing auto-posts without you clicking approve (important — don't fully automate posting until you trust the clip selection).
- Add error handling/retries for failed uploads and API rate-limit backoff.
- Add a `.env.example` and README so you can rebuild this on a new machine.
- **Done when:** the whole loop — URL in, review generated shorts, approve, they post, metrics show up — works without you touching the terminal.

---

## Notes to keep in mind as you go
- Get the Instagram API app review moving in week 5 even if you're not ready to code against it yet — review time is the biggest bottleneck in this whole project, not the coding.
- Keep the "approve before posting" step in v1. Fully autonomous posting is easy to add later once you trust the clip-selection quality.
- If a step ever feels like it needs a paid API to work well (e.g. local LLM picking bad moments), that's a tuning problem to solve with prompting/model choice first — don't reach for a paid API by default.
- If you plan to run football broadcasts or game footage (GTA 6 etc.) through the visual-based path, keep in mind that content is licensed/copyrighted to the broadcaster or publisher — clipping and reposting it is a different situation from clipping your own long-form video, and is worth thinking through separately from the technical build.
