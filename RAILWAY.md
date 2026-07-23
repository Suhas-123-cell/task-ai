# Deploying to Railway

## Combined single-service deployment (recommended)

One Railway service, built from the repo-root `Dockerfile`: FastAPI serves
both the API and the built React frontend from a single process, at one
URL, with no CORS configuration needed at all.

1. Railway → **New Project** → **Deploy from GitHub repo** → this repo.
2. Leave **Root Directory** as the repo root (don't set it to `backend` or
   `frontend`). Railway detects `railway.toml` at the root, which points at
   the Dockerfile.
3. **Settings → Volumes** → attach a volume mounted at `/app/data`. Without
   this, Railway's filesystem is ephemeral and every redeploy wipes the
   SQLite database and the vector store. (`docker-entrypoint.sh` runs
   knowledge-base ingestion at container *start*, not build time,
   specifically so it writes into this real, persisted volume rather than a
   throwaway build-time filesystem — and skips re-ingesting if the volume
   already has data, so restarts don't waste time re-embedding everything.)
4. **Settings → Variables** → set `GROQ_API_KEY` to your real key.
   `CORS_ORIGINS` is not needed in this mode — there's only one origin.
5. Deploy. **Settings → Networking → Generate Domain** gives you the one
   URL for everything: open it in a browser, and it's what goes in your
   demo video / submission.

This is what `railway.toml` (repo root), `Dockerfile`, and
`docker-entrypoint.sh` are for.

**Known issue and fix: OOM during first ingestion.** The full textbook PDFs
(Mitchell + Bishop, thousands of chunks) were found to get the ingestion
process killed by Railway's default container memory limit on first
deploy — the deploy log showed `running knowledge base ingestion...
Killed` repeating on every restart, the Linux OOM-killer's signature (no
Python traceback, since SIGKILL can't be caught). `docker-entrypoint.sh`
now runs `scripts/ingest_kb.py --skip-pdf` for the deployed container
specifically, ingesting only the lightweight original `.md` articles (a
few dozen chunks, seconds to embed, minimal memory) instead of the full
textbooks. **This means the deployed app is grounded in the original
articles, not the two committed textbook PDFs** — for the full
textbook-grounded experience (e.g. for your demo video), run locally
instead (`python scripts/ingest_kb.py`, no flag), or upgrade to a Railway
plan with more memory and remove `--skip-pdf` from `docker-entrypoint.sh`.

## Alternative: two separate services

If you'd rather run the frontend and backend as independent services (e.g.
to scale or redeploy them separately), `backend/railway.toml` and
`frontend/railway.toml` support that instead — **use one approach or the
other, not both** (don't create three Railway services from one repo).

1. **Backend service**: Root Directory = `backend`. Same Volume-at-`/app/data`
   requirement as above. Set `GROQ_API_KEY`, and `CORS_ORIGINS` to the
   frontend service's public URL (set this after step 2, once you have it).
2. **Frontend service**: Root Directory = `frontend`. Set
   `VITE_API_BASE_URL` to the backend's public URL **before the first
   build** — Vite bakes it into the built JS at build time, so setting it
   afterward does nothing until you trigger a rebuild.
3. Go back to the backend service and set `CORS_ORIGINS` to the frontend's
   URL from step 2, then redeploy the backend.

## Known limitation on either deployment mode

This app has **no authentication** and **no rate limiting** (documented in
README's "Known limitations" section) — fine for a local demo, but if a
Railway deployment (either mode) is left publicly reachable, anyone who
finds the URL can use it and drive real Groq API cost, or view any
candidate's data by guessing an ID. Consider this before leaving a public
deployment running longer than needed for grading/demo purposes.
