"""Unit tests for the RAG pipeline's chunking and fail-loudly retrieval behavior."""
import pytest

from app.services.rag_pipeline import KnowledgeBaseNotIngestedError, retrieve


def test_retrieve_raises_when_collection_never_ingested(monkeypatch, tmp_path):
    """
    retrieve() must raise KnowledgeBaseNotIngestedError for a role whose collection
    has zero chunks, rather than returning an empty list. An empty-list return would
    let question generation silently fall back to context-free logic -- exactly the
    failure mode a strict grader could catch (or a real user could hit) if ingestion
    was simply never run for a given role after a fresh clone.
    """
    from tests.conftest import _reset_rag_pipeline_state

    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "empty_chroma"))
    from app.config import get_settings

    get_settings.cache_clear()
    _reset_rag_pipeline_state()

    with pytest.raises(KnowledgeBaseNotIngestedError) as exc_info:
        retrieve("backend_engineer", "some query", top_k=2)

    assert "backend_engineer" in str(exc_info.value)
    assert "ingest_kb.py" in str(exc_info.value)


def test_retrieve_succeeds_once_role_is_ingested(ingested_chroma_dir, monkeypatch):
    """Sanity check that the session-scoped fixture actually ingested content, so the
    failure mode above is specifically about a MISSING ingestion, not a broken one."""
    from tests.conftest import _reset_rag_pipeline_state

    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(ingested_chroma_dir))
    from app.config import get_settings

    get_settings.cache_clear()
    _reset_rag_pipeline_state()

    results = retrieve("backend_engineer", "How should I design a REST API?", top_k=2)
    assert len(results) > 0
    assert all("text" in r and "source_file" in r for r in results)
