"""
End-to-end integration test of the full candidate -> session -> interview ->
report flow, exercised through the actual HTTP API (FastAPI TestClient) so it
covers routers, services, and the ORM together. Runs against the deterministic
fallback LLM path (no GROQ_API_KEY in the test environment), which is exactly
the path that had the topic-repetition bug this test guards against.
"""
SAMPLE_RESUME = b"""Jane Doe
Backend Engineer with 3 years of experience

Skills: Python, FastAPI, PostgreSQL, Docker, Redis, REST API design

Experience:
Backend Engineer, TechCorp (2022-2025)
- Built REST APIs using FastAPI and PostgreSQL
- Implemented caching layer with Redis
"""

# Broad, multi-topic answer: semantic chunking (see rag_pipeline.py) produces more
# topically distinct chunks than the old sliding-window chunker did, so a narrow
# single-topic canned answer now correctly scores weak against unrelated topics --
# which is the adaptive engine working *better*, not worse. This test is about
# verifying topic ADVANCEMENT on a strong answer, so the answer itself needs broad
# enough vocabulary to score reasonably regardless of which backend topic comes up.
ANSWER_TEXT = (
    "We use Redis as a shared cache in front of PostgreSQL, keying entries by request "
    "parameters and setting a TTL to bound staleness, invalidating on writes that touch "
    "that data so reads stay fast without serving badly stale results. We containerize "
    "the service with Docker, using small cache-friendly layers, and deploy it via a "
    "Kubernetes Deployment behind a Service, with a GitHub Actions CI/CD pipeline that "
    "runs the test suite and builds a tagged image before rollout. The REST API itself "
    "is built with FastAPI, validated with pydantic schemas, and covered by pytest "
    "integration tests against a real database."
)


def _upload_candidate(client, role="backend_engineer"):
    response = client.post(
        "/api/candidates",
        data={"target_role": role, "full_name": "Jane Doe"},
        files={"resume": ("resume.txt", SAMPLE_RESUME, "text/plain")},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_roles_endpoint_lists_three_roles(client):
    response = client.get("/api/roles")
    assert response.status_code == 200
    slugs = {r["slug"] for r in response.json()}
    assert slugs == {"ai_ml_engineer", "backend_engineer", "data_scientist"}


def test_candidate_upload_extracts_skills(client):
    candidate = _upload_candidate(client)
    assert candidate["target_role"] == "backend_engineer"
    assert "fastapi" in candidate["extracted_technologies"]
    assert candidate["experience_signals"]["years_experience"] == 3.0


def test_candidate_upload_rejects_unknown_role(client):
    response = client.post(
        "/api/candidates",
        data={"target_role": "astronaut", "full_name": "Jane Doe"},
        files={"resume": ("resume.txt", SAMPLE_RESUME, "text/plain")},
    )
    assert response.status_code == 400


def test_full_interview_flow_reaches_a_distinct_topic_report(client):
    candidate = _upload_candidate(client)

    start = client.post("/api/interview/sessions", json={"candidate_id": candidate["id"]})
    assert start.status_code == 201
    session_id = start.json()["session"]["id"]

    topics_seen = [start.json()["question"]["topic"]]
    is_complete = False

    for _ in range(10):  # hard cap so a bug can't infinite-loop the test
        response = client.post(f"/api/interview/sessions/{session_id}/answer", json={"answer_text": ANSWER_TEXT})
        assert response.status_code == 200, response.text
        body = response.json()
        is_complete = body["is_complete"]
        if body["next_question"]:
            topics_seen.append(body["next_question"]["topic"])
        if is_complete:
            break

    assert is_complete
    # Regression check: every question in a 5-question interview should probe a
    # different topic when every answer is strong (see test_query_builder.py for the
    # unit-level version of this same guarantee).
    assert len(set(topics_seen)) == len(topics_seen), f"topics repeated: {topics_seen}"

    report = client.get(f"/api/reports/{session_id}")
    assert report.status_code == 200
    body = report.json()
    assert len(body["qa_pairs"]) == 5
    assert 1.0 <= body["overall_score"] <= 5.0


def test_report_not_available_before_completion(client):
    candidate = _upload_candidate(client)
    start = client.post("/api/interview/sessions", json={"candidate_id": candidate["id"]})
    session_id = start.json()["session"]["id"]

    response = client.get(f"/api/reports/{session_id}")
    assert response.status_code == 409


def test_answering_completed_session_is_rejected(client):
    candidate = _upload_candidate(client)
    start = client.post("/api/interview/sessions", json={"candidate_id": candidate["id"]})
    session_id = start.json()["session"]["id"]

    for _ in range(10):
        response = client.post(f"/api/interview/sessions/{session_id}/answer", json={"answer_text": ANSWER_TEXT})
        if response.json()["is_complete"]:
            break

    late_answer = client.post(f"/api/interview/sessions/{session_id}/answer", json={"answer_text": ANSWER_TEXT})
    assert late_answer.status_code == 409


def test_starting_session_fails_loudly_when_role_not_ingested(monkeypatch, tmp_path):
    """
    A role whose Chroma collection was never ingested must fail loudly (503 with
    an actionable message), not silently generate a context-free fallback question.

    Deliberately does NOT use the `client` fixture: that fixture's Chroma dir has
    all three roles already ingested (see conftest.py's session-scoped
    ingested_chroma_dir), so this test builds its own fully isolated app instance
    pointed at an empty Chroma directory instead.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from tests.conftest import _reset_rag_pipeline_state

    empty_chroma_dir = tmp_path / "empty_chroma"
    db_path = tmp_path / "isolated.db"
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(empty_chroma_dir))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("GROQ_API_KEY", "")

    from app.config import get_settings

    get_settings.cache_clear()
    _reset_rag_pipeline_state()

    from app import database as database_module

    test_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    database_module.engine = test_engine
    database_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    database_module.init_db()

    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as isolated_client:
        upload = isolated_client.post(
            "/api/candidates",
            data={"target_role": "backend_engineer", "full_name": "Jane Doe"},
            files={"resume": ("resume.txt", SAMPLE_RESUME, "text/plain")},
        )
        assert upload.status_code == 201
        candidate_id = upload.json()["id"]

        response = isolated_client.post("/api/interview/sessions", json={"candidate_id": candidate_id})
        assert response.status_code == 503
        assert "ingest" in response.json()["detail"].lower()
        assert "backend_engineer" in response.json()["detail"]
