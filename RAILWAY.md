# Deploying to Railway

This is a two-service app (FastAPI backend + React frontend), so it needs
**two separate Railway services** from this one repo, each pointed at a
different subdirectory. Railway's native config format is TOML/JSON, not
YAML -- `backend/railway.toml` and `frontend/railway.toml` are the actual
files Railway reads.

## 1. Backend service

1. In Railway: **New Service → Deploy from GitHub repo** → this repo.
2. Set **Root Directory** to `backend`.
3. Railway will detect `backend/railway.toml` automatically (Nixpacks
   builder, installs `requirements.txt`, runs `scripts/ingest_kb.py` at
   build time, starts `uvicorn`).
4. **Attach a Volume** mounted at `/app/data`. Without this, Railway's
   filesystem is ephemeral -- every redeploy would silently wipe the
   SQLite database (all interview history) and the Chroma vector store,
   forcing a full re-ingestion on every deploy.
5. Set environment variables (Settings → Variables):
   - `GROQ_API_KEY` -- your real key, for real LLM-quality questions/scoring.
   - `CORS_ORIGINS` -- the frontend service's public URL once you have it
     (step 2.3 below); update this after creating the frontend service.
6. Deploy. Note the backend's public URL (Settings → Networking →
   Generate Domain) -- you'll need it for the frontend.

## 2. Frontend service

1. **New Service → Deploy from GitHub repo** → this repo again.
2. Set **Root Directory** to `frontend`.
3. Set environment variable `VITE_API_BASE_URL` to the backend's public URL
   from step 1.6 (e.g. `https://your-backend.up.railway.app`) **before the
   first build** -- Vite bakes env vars into the built JS bundle at build
   time, so setting this after deploying does nothing until you trigger a
   rebuild.
4. Railway will detect `frontend/railway.toml` (builds with `npm run
   build`, serves the static output with `serve`).
5. Deploy. Note the frontend's public URL, and go back to the backend
   service to set `CORS_ORIGINS` to it (step 1.5) -- then redeploy the
   backend so the new CORS origin takes effect.

## Known limitation on Railway specifically

This app has **no authentication** and **no rate limiting** (documented in
README's "Known limitations" section) -- fine for a local demo, but if this
Railway deployment is left publicly reachable, anyone can hit the
Groq-backed endpoints and drive real API cost, or view any candidate's
data by guessing an ID. Consider this before leaving a public deployment
running longer than needed for grading/demo purposes.
