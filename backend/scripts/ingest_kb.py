#!/usr/bin/env python
"""
CLI entry point to (re-)build the vector store from the knowledge_base/
directory. Run this once before starting the API, and again any time a
knowledge base document is added, removed, or edited.

Usage:
    python scripts/ingest_kb.py                        # ingest all roles, all files
    python scripts/ingest_kb.py ai_ml_engineer          # ingest a single role
    python scripts/ingest_kb.py --skip-pdf              # .md/.txt only, all roles
    python scripts/ingest_kb.py --skip-pdf ai_ml_engineer

--skip-pdf exists for memory-constrained deploy environments: the full
textbook PDFs (Mitchell + Bishop, thousands of chunks) require enough RAM to
load torch/transformers plus hold that corpus during embedding, which was
observed to OOM-kill the ingestion process on a constrained container
(Railway's default memory limit) -- see docker-entrypoint.sh, which passes
this flag specifically for that reason. Local development, with no such
constraint, omits the flag and gets the full textbook-grounded experience.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import KNOWLEDGE_BASE_DIR  # noqa: E402
from app.services.rag_pipeline import ingest_role  # noqa: E402


def main() -> None:
    args = sys.argv[1:]
    skip_pdf = "--skip-pdf" in args
    requested_roles = [a for a in args if a != "--skip-pdf"]

    extensions = (".md", ".txt") if skip_pdf else (".md", ".txt", ".pdf")
    available_roles = sorted(p.name for p in KNOWLEDGE_BASE_DIR.iterdir() if p.is_dir())
    roles = requested_roles or available_roles

    print(f"Ingesting knowledge base for roles: {roles} (extensions: {extensions})")
    total = 0
    for role in roles:
        if role not in available_roles:
            print(f"  [skip] '{role}' has no knowledge_base directory")
            continue
        count = ingest_role(role, extensions=extensions)
        total += count
        print(f"  [ok] {role}: {count} chunks embedded and stored")

    print(f"Done. {total} total chunks across {len(roles)} role(s).")


if __name__ == "__main__":
    main()
