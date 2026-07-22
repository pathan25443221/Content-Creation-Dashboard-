# Rules: Content Dashboard

Working rules for building and extending this project. Anything not covered here should default to the constraints in `PRD.md` (free/open-source, self-hosted, human-approves-before-posting).

## 1. What to use

**Video/audio processing**
- `yt-dlp` for downloading — actively maintained, handles YouTube reliably.
- `ffmpeg` for all cutting, cropping, caption burning. Don't reach for a second video library alongside it.
- `faster-whisper` for transcription (local, CPU-friendly). Use the smallest model that gives acceptable accuracy before jumping to a bigger one.

**AI / clip selection**
- `Ollama` for any local LLM or vision-model use (clip selection, frame tagging).
- `pyannote.audio` for speaker diarization, only when a video actually has multiple speakers.
- `librosa` for audio energy analysis, `PySceneDetect` for motion/scene detection.

**Backend / data**
- `FastAPI` for the dashboard backend.
- `SQLite` for local development, `Postgres` if/when running on a VPS.
- Plain SQL migrations or a lightweight ORM (e.g. SQLModel) — avoid heavy ORMs with a large learning curve for a single-operator project.

**Frontend**
- Plain HTML + Chart.js, or React with a minimal component set. No need for a large design system for a personal dashboard.

**Publishing**
- Only the official YouTube Data API and Instagram Graph API. No unofficial/reverse-engineered endpoints for posting.

## 2. What to avoid

- **No paid AI APIs** (OpenAI, Gemini, Anthropic, etc.) as a required dependency. If a feature only works well with a paid API, that's a signal to improve the local model/prompt first, not to add a paid dependency by default. If a paid option is ever added, it must be optional and clearly marked, never the default path.
- **No scraping or unofficial APIs** for posting or reading platform data (no headless-browser Instagram/TikTok automation, no reverse-engineered private endpoints). Official APIs only — unofficial methods get accounts banned and aren't something this project should rely on.
- **No message brokers/heavy infra** (Redis, Kafka, Celery) at this scale — a database-backed queue table is enough. Don't add infrastructure the project doesn't need yet.
- **No multi-tenant auth system** — this is a single-operator tool, not a SaaS product. Don't build user accounts, roles, or org structures speculatively.
- **No committing secrets** — API keys, OAuth tokens, and credentials never go in source control. `.env` and `publisher/credentials/` are gitignored; only `.env.example` with placeholder values is committed.
- **No fully autonomous posting** — don't remove the review/approve step to "streamline" the flow. This is a deliberate boundary, not a missing feature.
- **No processing of content the operator doesn't have rights to** as a default assumption — the visual-based path especially should not be pointed at licensed broadcast footage or copyrighted game content without the operator having thought through that separately (see PRD risks).

## 3. Error handling

- **Every external call (API, ffmpeg, model inference) must be wrapped and fail loudly, not silently.** A failed transcription or upload should surface a clear error in logs/dashboard, not just skip and continue.
- **Retries with backoff** for network calls (platform APIs, download failures) — a transient failure shouldn't kill the whole pipeline run. Cap retries (e.g. 3 attempts) rather than retrying indefinitely.
- **Rate-limit awareness is not optional.** Before adding any call to YouTube or Instagram's API, check the current known limits (quota units/day, posts/24h) and make sure `queue.py` respects them. A rate-limit error should pause and back off, not be treated as a generic failure.
- **Partial failure should not corrupt state.** If a video fails at the clip-selection step, it should be marked failed in the database, not silently dropped — the operator should be able to see what failed and why.
- **No swallowing exceptions with a bare `except: pass`.** Log the actual error with enough context (video ID, stage, timestamp) to debug later.
- **Idempotency for publishing**: re-running a job for an already-posted clip should not double-post — check `posts` table state first.

## 4. Boundaries for AI components

These apply to every AI step in the pipeline (clip selection, vision tagging, diarization-adjacent reasoning):

- **AI proposes, the operator decides.** The LLM/vision model's output is always a *candidate* (clip timestamps, tags, reasons) — never auto-published without a human approval step, per PRD requirements.
- **No claim of virality prediction.** Prompts and any user-facing copy should describe clip selection as heuristic-based (hooks, self-contained points, audio/motion spikes), not as "predicting what will go viral." Don't oversell what the model is actually doing.
- **Keep AI decisions inspectable.** Every clip selection should come with the one-line reason the model gave — this is a debugging and trust tool, not just a nice-to-have. Don't strip it out of the output.
- **Local models only, by default**, per the free/open-source constraint — see Section 2.
- **No AI-generated captions/titles get auto-published without review** — same rule as the clips themselves. A model can draft a title; the operator approves or edits it.
- **Feed real outcomes back deliberately, not automatically.** If you build a feedback loop (using past post performance to improve future clip selection, as discussed in the PRD), that should be a reviewed, occasional process — not the model silently retraining or reweighting itself on live data without visibility into what changed.

## 5. When in doubt

If a decision isn't covered above, default to whichever option is: (1) free or already-in-stack, (2) reversible/simple to change later, and (3) keeps a human in the loop before anything goes public. Optimize for something you can debug and maintain solo, not for maximum automation.
