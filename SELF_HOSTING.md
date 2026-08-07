# Self-hosting ClipForge

This walks you through getting ClipForge running on your own machine, using your own accounts. Nobody else's setup or credentials are involved — every step below creates something that belongs to you.

Budget 1–2 hours the first time, mostly waiting on account approvals rather than active work.

## 0. Before you start

You'll need:
- A computer that can run Python, Docker, and a local LLM reasonably (8GB+ RAM minimum; more helps Whisper/Ollama run faster, but nothing here strictly requires a GPU).
- A Google account (for YouTube).
- A Facebook/Instagram account, converted to Business or Creator (for Instagram) — see Step 3, this can't be a personal account.
- About 15–20 minutes of *waiting* built into your week for Instagram's app review — it's not instant, so it's worth starting that step early even if you circle back to it.

## 1. Clone and install base dependencies

```bash
git clone https://github.com/<your-username>/clipforge.git
cd clipforge
cp .env.example .env
```

Install the non-Python tools first:
- **ffmpeg** — required for all video cutting/rendering. Install via your OS package manager (`brew install ffmpeg` on macOS, `apt install ffmpeg` on Ubuntu/Debian, or download a build for Windows).
- **Docker + Docker Compose** — used to run Postgres locally without installing it directly.

Then the Python environment:
```bash
python -m venv venv
source venv/bin/activate   # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## 2. Set up local AI (Whisper + Ollama)

```bash
bash scripts/setup_local_llm.sh
```

This pulls a local LLM through Ollama (default: Llama 3.1 8B) and downloads the Whisper model used for transcription. Both run entirely on your machine — no API key, no per-use cost.

If you'd rather do it manually:
```bash
# Install Ollama from https://ollama.com, then:
ollama pull llama3.1:8b
```
Whisper models download automatically the first time `speech_based/transcribe.py` runs.

## 3. Connect your YouTube account

1. Go to the [Google Cloud Console](https://console.cloud.google.com) and create a new project (any name — e.g. "clipforge-yourname").
2. In the project, go to **APIs & Services → Library**, search for **YouTube Data API v3**, and enable it.
3. Go to **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
   - If prompted, configure the OAuth consent screen first: choose **External**, fill in an app name and your email, and add your own Google account as a **test user** (this lets you use the app immediately without waiting for Google's review, as long as you're the only user).
   - Application type: **Desktop app** (simplest for local/self-hosted use).
4. Download the resulting credentials JSON and save it as `publisher/credentials/youtube_client_secret.json`.
5. Run the one-time auth script:
   ```bash
   python publisher/youtube_auth_setup.py
   ```
   This opens a browser window, asks you to log into your own YouTube account, and saves an access/refresh token locally in `publisher/credentials/`.

**Note on quota:** your new project gets a default 10,000 units/day, which is your own personal allocation (not shared with anyone else, since it's your own Google Cloud project). Each upload costs roughly 1,600 units — plenty for personal use.

## 4. Connect your Instagram account

This one has more setup because of Meta's requirements — it's the slowest step, so it's worth doing this early and letting it run in the background while you do other steps.

1. **Convert your Instagram account** to a Business or Creator account (Instagram app → Settings → Account type) and **link it to a Facebook Page** — the API does not work with personal accounts at all.
2. Go to [developers.facebook.com](https://developers.facebook.com) and create a new app (type: **Business**).
3. Add the **Instagram Graph API** product to your app.
4. Under **App Review**, request the `instagram_content_publish` permission. For a single self-hosted use case (you posting to your own account), Meta typically allows this under **development mode** with your own account added as a **test user/tester** on the app — this avoids needing full public review, since you're not serving other people's accounts.
5. Copy your **App ID** and **App Secret** into `.env` (`META_APP_ID`, `META_APP_SECRET`).
6. Run:
   ```bash
   python publisher/instagram_auth_setup.py
   ```
   Follow the printed URL, authorize your own account, and the resulting token saves locally.

**If you get stuck on review:** Meta's dev-mode + tester-account path (rather than full public app review) is almost always enough for a self-hosted single-account setup — you generally only need full review if you intend to post on behalf of *other* people's accounts, which self-hosting for yourself doesn't require.

## 5. Start the database and backend

```bash
docker-compose up -d      # starts Postgres
bash scripts/init_db.sh   # creates tables
uvicorn dashboard.backend.main:app --reload
```

## 6. Start the frontend

```bash
cd dashboard/frontend
npm install
npm run dev
```

Open the printed local URL (typically `http://localhost:5173`) — you should see the Overview screen.

## 7. Test it end to end

1. Paste a short talking-head YouTube URL into **Generate Clip**.
2. Watch it move through download → transcribe → select → render.
3. Approve a clip in **Review Queue**.
4. Confirm it posts to your own YouTube/Instagram account.
5. Check **Analytics** after a little while to see metrics start populating.

If any step fails, check the terminal running the backend first — errors are logged there per `RULES.md`'s "fail loudly" principle, not swallowed silently.

## Troubleshooting quick reference

| Symptom | Likely cause |
|---|---|
| Ollama step hangs or errors | Ollama not installed/running — check `ollama list` shows your pulled model |
| YouTube upload fails with `quotaExceeded` | Your own project's daily 10,000-unit quota is used up — resets at midnight Pacific time |
| Instagram auth fails immediately | Account isn't Business/Creator, or isn't linked to a Facebook Page yet |
| Whisper transcription is very slow | Expected on CPU-only machines for long videos — try a smaller Whisper model size |
| Posts show "pending" forever | Check `publisher/queue.py` logs — usually a token needing refresh |

## You're on your own instance now

Everything above created accounts, tokens, and quota that belong to you alone. There's no shared backend, no dependency on the original maintainer's infrastructure, and no data leaving your machine except the direct calls to YouTube/Instagram's own APIs with your own credentials.

If this was useful, a star on the [GitHub repo](https://github.com/<your-username>/clipforge) helps other people find it — never required, just appreciated.
