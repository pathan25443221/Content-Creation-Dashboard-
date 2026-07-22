# Phases: Content Dashboard

A milestone-level view of the project. This sits above `shorts-dashboard-build-plan.md` (which has the week-by-week task breakdown) — use this file to track overall progress and to know what's explicitly deferred to later.

## Phase 0 — Setup
- Repo scaffolding, `.env.example`, `docker-compose.yml`, base folder structure in place.
- Local dev environment working: Python env, `ffmpeg`, `yt-dlp`, Ollama installed and a small model pulled.
- **Exit criteria:** a fresh clone of the repo can be set up and run following the README, no manual guesswork.

## Phase 1 — Generation (speech-based path)
- Download a video, transcribe it locally, select 2–4 candidate clips using a local LLM, render them as vertical mp4s with captions.
- Covers: talking-head, podcast, tutorial, narrated-vlog content only.
- **Exit criteria:** one command chain takes a talking-head YouTube URL and produces usable vertical clips in `generator/output/`.

## Phase 2 — Generation (visual-based path)
- Add audio-energy and motion-detection based clip selection for non-speech content (sports, gameplay, silent video).
- Output shape matches Phase 1's so `render.py` doesn't need to branch.
- **Exit criteria:** a football/gameplay clip produces usable candidate shorts via this path.

## Phase 3 — Publishing
- Connect YouTube and Instagram accounts, build the review/approve queue, publish approved clips through official APIs.
- Add the rate-limit-aware job queue so multi-platform posting doesn't collide.
- **Exit criteria:** an approved clip posts to both YouTube Shorts and Instagram Reels via script, respecting each platform's constraints.

## Phase 4 — Analytics
- Schema for videos/clips/posts/metrics, scheduled polling of each platform's stats endpoints, historical metric storage.
- **Exit criteria:** metrics for posted clips accumulate automatically without manual checking of each platform's app.

## Phase 5 — Dashboard
- Backend API over the shared database, frontend views: clip list/grid with per-platform metrics, at least one performance chart.
- **Exit criteria:** the operator can see every generated clip, where it's posted, and how it's performing, from one local webpage.

## Phase 6 — Integration & hardening
- Wire all three stages into one flow: generate → review → approve → publish → track.
- Add retries/backoff, idempotent publishing, and clear failure states per `RULES.md`.
- **Exit criteria:** the full loop runs end to end without touching the terminal beyond the initial URL input and approval clicks.

---

## Later / explicitly deferred (not in v1)

These are reasonable next steps once the phases above are solid, but are intentionally out of scope until then:

- **Feedback loop**: using real post performance to refine clip-selection prompts (mentioned in PRD as a future direction, not a v1 feature).
- **Additional platforms** beyond YouTube and Instagram (e.g. TikTok, if reconsidered later).
- **Auto-detection of speech vs. visual path** (`router.py` currently expects a manual flag — smart auto-routing based on transcript quality/audio content is a later refinement).
- **Fully autonomous posting** (removing the approval step) — only worth considering once clip-selection quality is proven trustworthy over time; see the explicit boundary in `RULES.md`.
- **Vision-tagging step** (`vision_tag.py`) for the visual-based path — listed as an optional stretch goal, not required for Phase 2's exit criteria.
- **Multi-operator/team support** — out of scope; this remains a single-operator tool per the PRD.

## How to use this file
Check a phase off only when its exit criteria are met, not when the code merely exists — the exit criteria are the actual bar. If a phase is taking noticeably longer than expected, that's a signal to descope rather than to skip its exit criteria.
