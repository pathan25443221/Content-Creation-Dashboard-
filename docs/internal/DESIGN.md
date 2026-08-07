# Design: Content Dashboard

UI/UX reference for the dashboard — the one piece of this project with an actual interface. Covers screens, user flow, component states, and visual style. Pairs with `ARCHITECTURE.md` (data/backend) and `PRD.md` (feature scope).

## 1. Design principles

- **Built for one operator, not a general audience.** Optimize for speed of review and clarity of data over polish or onboarding flows — no tutorials, no marketing copy, no empty-state sales pitches.
- **Review is a first-class screen, not a modal.** Approving/rejecting clips before they post is a core action per `RULES.md`, so it gets a proper dedicated view, not an afterthought popup.
- **Status must always be visible.** Every clip and post has a clear state (processing, ready for review, posted, failed) — the operator should never have to guess whether something worked.
- **Data density over decoration.** This is an internal tool. Favor tables/grids with real numbers over large illustrative cards.

## 2. Screens

### 2.1 Home / Overview
- Summary at the top: total clips generated, pending review count, posts published (last 7 days), quick aggregate stats (total views/likes across all clips).
- Recent activity list: last N clips generated/posted/failed, each with a status badge.
- Primary action: "Generate from URL" input, front and center.

### 2.2 Generate
- Single input: paste a video URL (or upload a local file).
- Manual path selector for now: Speech-based / Visual-based (per `router.py` in Phase 1–2 — auto-detection is deferred, see `PHASES.md`).
- On submit: show a processing state (download → transcribe/analyze → select clips → render), with the current step highlighted so the operator knows it's alive, not stuck.
- On completion: route to the Review screen for that video's generated clips.

### 2.3 Review queue
- Grid of generated clips awaiting approval. Each card shows:
  - Video preview (thumbnail or inline player)
  - The one-line reason the AI selected this segment (per `RULES.md` — always show this, never hide it)
  - Start/end timestamps
  - Editable title/caption field
  - Platform checkboxes (YouTube / Instagram) for where to post it
  - Actions: Approve & queue, Edit, Reject
- Rejected clips are dismissed, not deleted — kept for reference with a "rejected" status.
- Bulk approve is fine for clips from the same source video; no bulk-approve across unrelated videos (keeps review deliberate).

### 2.4 Posts / Library
- Table of every clip ever generated, filterable by status (pending, approved, posted, failed) and by platform.
- Columns: thumbnail, title, source video, platform(s), posted date, status.
- Clicking a row opens the clip detail view.

### 2.5 Clip detail
- Video preview, full metadata (source video, timestamps, AI-selected reason, edit history if the title was changed).
- Per-platform post status and a link to the live post once published.
- Metrics panel (see 2.6) scoped to this one clip.

### 2.6 Analytics
- Per-clip metrics: views, likes, comments, reach, broken out by platform.
- One time-series chart per clip or per platform (views over time) — start simple, expand later.
- Sort/filter the clip library by a metric (e.g. "show my best performing clips") to make the feedback loop mentioned in `PHASES.md` practical later, even though the loop itself isn't built in v1.

## 3. Core user flow

```
Home ──▶ Generate (paste URL, pick path) ──▶ processing state
                                                  │
                                                  ▼
                                          Review queue (approve/edit/reject)
                                                  │
                                                  ▼
                                     queued ──▶ posted (via publisher)
                                                  │
                                                  ▼
                                          Posts/Library + Clip detail
                                                  │
                                                  ▼
                                          Analytics (metrics roll in over time)
```

The operator's actual weekly loop, once the system is running, is: check Home for anything pending review → review queue → occasionally check Analytics to see what's working.

## 4. Component states to design for

Every list/card component needs to handle:
- **Empty** — no clips yet ("nothing generated yet" + the Generate action, not a sales pitch).
- **Loading/processing** — clip generation and metric fetches both take time; show which step is active, not just a generic spinner.
- **Success** — the normal populated state.
- **Failed** — a clip, upload, or metrics fetch failed. Show what failed and why (per `RULES.md`'s "fail loudly" rule), with a retry action where applicable.
- **Rate-limited/waiting** — a post is queued but waiting due to platform rate limits. Distinguish this from a failure — it's expected behavior, not an error.

## 5. Visual style

- Plain, functional UI — a data table with badges beats a card-heavy dashboard for this use case.
- Status badges use consistent colors across the whole app: e.g. gray = pending, blue = processing, green = posted, red = failed, amber = rate-limited/waiting.
- Charts: keep to line charts (metrics over time) and simple bar comparisons (clip vs clip) — no need for anything more elaborate for a single-operator tool.
- No dark patterns, no engagement-bait UI (streaks, badges, gamification) — this is a utility, not a consumer product.

## 6. Out of scope for v1 design
- No mobile-optimized layout — desktop-first, since this is a personal operating tool run from a dev machine.
- No multi-user permissions/views — single operator, so no role-based UI variations.
- No onboarding flow — the README covers setup; the UI itself doesn't need a first-run wizard.
