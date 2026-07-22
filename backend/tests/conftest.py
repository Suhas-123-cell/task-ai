"""
Shared pytest fixtures: an isolated, file-based test DB, and an isolated,
pre-ingested Chroma vector store, so the test suite never depends on (or
mutates) a developer's real backend/data/{app.db,chroma}.
"""
import os
import hashlib
import tempfile
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROLES_TO_INGEST = ("ai_ml_engineer", "backend_engineer", "data_scientist")


class _TestEmbeddingModel:
    """Small deterministic embedding model for tests.

    Tests should validate our ingestion/retrieval plumbing, not depend on
    Hugging Face network/cache state. This keeps the isolated Chroma fixture
    fast, deterministic, and fully offline.
    """

    dimension = 32

    def encode(self, texts, show_progress_bar=False, normalize_embeddings=False):
        vectors = []
        for text in texts:
            vector = np.zeros(self.dimension, dtype=np.float32)
            for token in str(text).lower().split():
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                vector[digest[0] % self.dimension] += 1.0
            if normalize_embeddings:
                norm = np.linalg.norm(vector)
                if norm:
                    vector = vector / norm
            vectors.append(vector)
        return np.vstack(vectors)


def _reset_rag_pipeline_state():
    """
    Force rag_pipeline to re-read settings and rebuild its lazy Chroma client on
    the next call.

    rag_pipeline.py caches `settings` and the Chroma client as module-level
    globals for performance (see that module's docstring). That's fine in the
    running app, but it means simply changing CHROMA_PERSIST_DIR via an env var
    and calling get_settings.cache_clear() is NOT enough in tests: the already-
    created Chroma client singleton would keep silently pointing at whichever
    directory was active the first time it was built. This must be called
    every time CHROMA_PERSIST_DIR changes between fixtures/tests.
    """
    from app.config import get_settings
    from app.services import rag_pipeline

    rag_pipeline.settings = get_settings()
    rag_pipeline._chroma_client = None
    rag_pipeline._embedding_model = _TestEmbeddingModel()


@pytest.fixture(scope="session")
def ingested_chroma_dir(tmp_path_factory):
    """
    Ingest all three real knowledge_base/ directories into an isolated, temporary
    Chroma store once per test session. Explicit and deterministic: tests do not
    rely on whatever a developer happens to have already ingested locally.
    """
    chroma_dir = tmp_path_factory.mktemp("chroma_test")
    os.environ["CHROMA_PERSIST_DIR"] = str(chroma_dir)

    from app.config import get_settings

    get_settings.cache_clear()
    _reset_rag_pipeline_state()

    from app.services.rag_pipeline import ingest_role

    for role in ROLES_TO_INGEST:
        # .md/.txt only, not .pdf: the real knowledge_base/ai_ml_engineer directory
        # now also contains two full real textbook PDFs (thousands of chunks each);
        # ingesting those on every test session would balloon the suite from ~12s to
        # several minutes for no test-value gain, since the hand-written articles
        # already exercise the same chunking/retrieval code paths the tests care
        # about. See rag_pipeline.load_role_documents()'s docstring for more detail.
        count = ingest_role(role, extensions=(".md", ".txt"))
        assert count > 0, f"Expected fixture ingestion for '{role}' to produce chunks"

    return chroma_dir


@pytest.fixture()
def client(monkeypatch, ingested_chroma_dir):
    tmp_dir = tempfile.mkdtemp()
    db_path = Path(tmp_dir) / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(ingested_chroma_dir))
    # Force the deterministic fallback LLM path regardless of what's in a real
    # backend/.env on disk. Without this, once a developer adds a real GROQ_API_KEY
    # for local use, the test suite silently starts exercising the real (paid,
    # non-deterministic) LLM instead of the fallback logic it's meant to test --
    # which is exactly what happened here: a real key in .env made a canned test
    # answer get correctly (and non-deterministically) scored low by the real model,
    # which looked like a topic-advancement regression but was actually the tests
    # accidentally depending on un-isolated local environment state.
    monkeypatch.setenv("GROQ_API_KEY", "")

    from app import database as database_module
    from app.config import get_settings

    get_settings.cache_clear()
    _reset_rag_pipeline_state()

    test_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    database_module.engine = test_engine
    database_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    from app.main import app

    database_module.init_db()

    with TestClient(app) as test_client:
        yield test_client

    os.remove(db_path) if db_path.exists() else None
