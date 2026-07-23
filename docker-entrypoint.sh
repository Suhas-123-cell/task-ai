#!/bin/sh
# Runs at container START, not at build time: Railway's persistent Volume
# (mounted at /app/data) only exists once the container actually starts, so
# ingestion must happen here to write into the real, persisted vector store
# -- ingesting during the Docker *build* would silently write into a
# throwaway build-time filesystem, and the running container would start
# with an empty (or stale) volume every time.
#
# Only ingests if the vector store looks empty, so a container restart
# doesn't needlessly re-embed the entire knowledge base every time (ingestion
# is otherwise idempotent -- see rag_pipeline.ingest_role's upsert -- but
# still costs real time on a full textbook-sized corpus). Delete
# /app/data/chroma on the volume to force a fresh re-ingestion.
set -e

if [ ! -d "/app/data/chroma" ] || [ -z "$(ls -A /app/data/chroma 2>/dev/null)" ]; then
  echo "No existing vector store found at /app/data/chroma -- running knowledge base ingestion..."
  python scripts/ingest_kb.py
else
  echo "Vector store already present at /app/data/chroma -- skipping ingestion."
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
