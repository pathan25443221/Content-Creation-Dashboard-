# PRD: Content Dashboard

## 1. Overview

A self-hosted, free/open-source system that takes a long-form video, generates short-form vertical clips from it, publishes those clips to connected social accounts, and tracks their performance in a single dashboard — replacing the manual work of clipping, uploading to each platform separately, and checking each app for stats.

## 2. Problem statement

Repurposing long videos into shorts is effective for reach but tedious to do manually: finding the good moments, cutting and captioning them, uploading to multiple platforms one by one, and checking analytics across separate apps. Existing tools that automate this (Opus Clip, Vidyo.ai, etc.) are paid SaaS products with subscription costs. There's no requirement to use a paid service — the same pipeline can be built with open-source components and official free-tier platform APIs.

## 3. Target user

- A solo creator or small team managing their own YouTube/Instagram presence, without a budget for paid clipping/scheduling tools.
- Comfortable running scripts locally / self-hosting (not a no-code end user) — this is a personal or small-scale tool, not a multi-tenant SaaS product.
- Posts a mix of talking-head/podcast/tutorial content and, potentially, non-speech content (gameplay, sports clips).

## 4. Goals

- Turn a video URL into 2–4 usable vertical short clips without manual editing.
- Publish clips to YouTube and Instagram without manually re-uploading in each app.
- See likes, views, reach, and comments for every posted clip in one dashboard, without opening each platform separately.
- Do all of the above using free, open-source, or official free-tier tools only — no required paid subscriptions.

## 5. Non-goals (out of scope for v1)

- Not a multi-user SaaS product — single-operator use only.
- Not attempting to predict virality — clip selection uses heuristics (hooks, punchlines, audio/motion spikes), not a trained engagement-prediction model.
- Not supporting every social platform — v1 targets YouTube and Instagram only.
- Not fully autonomous posting — every generated clip is reviewed and approved by the operator before it goes live.
- Not handling licensed/third-party footage (sports broadcasts, copyrighted game footage) as a supported use case — the operator is responsible for using content they have rights to.

## 6. Features

### 6.1 Clip generation
- Accept a YouTube URL or local video file as input.
- **Speech-based path** (talking-head, podcast, tutorial, vlog-with-narration content):
  - Transcribe audio locally (Whisper).
  - Optionally identify speakers in multi-speaker content (diarization).
  - Use a local LLM to identify 2–4 candidate segments based on hooks, self-contained points, punchlines, or emotional peaks.
- **Visual-based path** (sports, gameplay, silent/non-speech content):
  - Detect audio energy spikes (crowd noise, explosions, big hits).
  - Detect high visual motion/scene-change moments.
  - Combine both signals to propose candidate segments.
- Render selected segments: cut, crop to 9:16, burn in captions (speech path).
- Output: 2–4 finished vertical video files per source video.

### 6.2 Publishing
- Connect YouTube and Instagram accounts via their official APIs (OAuth).
- Review queue: operator sees generated clips before anything is posted, can approve, reject, or edit title/caption.
- Publish approved clips to selected platform(s).
- Respect each platform's constraints (Instagram Business/Creator account requirement, Reels duration window, daily post caps; YouTube Data API quota).
- Queue/schedule posts so multiple platform uploads don't collide or exceed rate limits.

### 6.3 Analytics
- Store every posted clip with its platform, post ID, and post time.
- Periodically fetch performance metrics per clip: views, likes, comments, reach (where available per platform).
- Dashboard view: list/grid of all clips with per-platform metrics, and at least one visualization (e.g., views over time).
- Historical data retained so performance can be compared across clips over time.

## 7. Technical constraints

- All components must be free or open-source, or use official platform APIs within their free tier — no required paid subscriptions or paid API credits.
- AI components (transcription, clip selection, vision tagging) run locally (Whisper, Ollama) rather than via paid cloud APIs.
- Self-hosted: runs on the operator's own machine or a free/low-cost VPS; no dependency on a hosted commercial backend.

## 8. Success criteria (v1)

- A talking-head video can go from URL to 2–4 posted, captioned vertical clips on YouTube and Instagram with no manual video editing.
- A non-speech video (e.g., gameplay) can produce usable candidate clips via the audio/motion path.
- Posted clip performance (views/likes/reach) is visible in the dashboard within a few hours of posting, without checking each platform's app directly.
- The entire pipeline runs without incurring subscription or paid-API costs under normal personal-use volume.

## 9. Risks / open questions

- Free local AI models (Whisper, small local LLMs) are less accurate than paid cloud models — clip selection quality may need iteration/prompt tuning over time.
- Instagram and platform API approval/review timelines are outside the project's control and can delay the publishing feature.
- Clipping and posting third-party or licensed footage (sports broadcasts, game publisher content) carries copyright/ToS risk that this tool does not manage — it's on the operator to source content appropriately.
- Analytics accuracy is bounded by what each platform's API exposes (e.g., Instagram Insights requires a minimum follower count to return data).
