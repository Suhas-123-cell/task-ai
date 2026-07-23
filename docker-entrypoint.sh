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
# still costs real time and memory on a large corpus). Delete
# /app/data/chroma on the volume to force a fresh re-ingestion.
#
# --skip-pdf: the full textbook PDFs (Mitchell + Bishop, thousands of
# chunks) were found to OOM-kill this ingestion step on Railway's default
# container memory -- confirmed directly from the deploy logs ("running
# knowledge base ingestion... Killed", the classic Linux OOM-killer
# signature, repeating on every restart with no other error). Ingesting
# only the lightweight original .md articles here gives a working,
# low-memory RAG deployment instead of a permanent crash loop; the full
# textbook-grounded experience remains available locally (run
# `python scripts/ingest_kb.py` without this flag, where memory isn't
# constrained the same way).
set -e

if [ ! -d "/app/data/chroma" ] || [ -z "$(ls -A /app/data/chroma 2>/dev/null)" ]; then
  echo "No existing vector store found at /app/data/chroma -- running knowledge base ingestion (--skip-pdf, see comment above)..."
  python scripts/ingest_kb.py --skip-pdf
else
  echo "Vector store already present at /app/data/chroma -- skipping ingestion."
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
