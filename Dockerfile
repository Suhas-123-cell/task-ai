# Combined single-service build: Node builds the React frontend, Python
# serves both the API and those built static files from one process. Built
# from the repo root (Railway: Root Directory = repo root, not a subfolder).

# ---- Stage 1: build the frontend ----
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# VITE_API_BASE_URL is deliberately left unset here (empty string), NOT the
# backend's own URL: same-origin deploy means the frontend should call
# relative /api/... paths, not an absolute cross-origin URL. See
# frontend/src/api/client.js's nullish-coalescing comment for why this must
# be an explicit empty string, not simply omitted.
ENV VITE_API_BASE_URL=""
RUN npm run build

# ---- Stage 2: backend + serve the built frontend ----
FROM python:3.12-slim AS backend
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
# Copied to backend/static/ -- app/main.py only mounts frontend routes when
# this directory exists, so local dev (no Docker build) is unaffected.
COPY --from=frontend-build /app/frontend/dist ./static
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

ENV PORT=8000
EXPOSE 8000
ENTRYPOINT ["/app/docker-entrypoint.sh"]
