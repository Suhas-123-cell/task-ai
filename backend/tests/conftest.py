"""Shared pytest fixtures: an isolated, file-based test DB per test session."""
import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def client(monkeypatch):
    tmp_dir = tempfile.mkdtemp()
    db_path = Path(tmp_dir) / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
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
    test_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    database_module.engine = test_engine
    database_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    from app.main import app

    database_module.init_db()

    with TestClient(app) as test_client:
        yield test_client

    os.remove(db_path) if db_path.exists() else None
