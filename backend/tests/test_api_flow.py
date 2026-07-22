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
