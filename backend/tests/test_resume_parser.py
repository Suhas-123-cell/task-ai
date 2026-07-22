"""Unit tests for resume text extraction and entity matching."""
from app.services.resume_parser import extract_experience_signals, extract_matched_terms, parse_resume

SAMPLE_RESUME = """
Jane Doe
Backend Engineer with 4 years of experience

Skills: Python, FastAPI, PostgreSQL, Docker, Redis

Experience:
Senior Backend Engineer, TechCorp
"""


def test_extract_matched_terms_is_case_insensitive():
    terms = extract_matched_terms("I use PYTHON and Docker daily", ["python", "docker", "kubernetes"])
    assert "python" in terms
    assert "docker" in terms
    assert "kubernetes" not in terms


def test_extract_matched_terms_respects_word_boundaries():
    # "java" must not match inside "javascript"
    terms = extract_matched_terms("I write javascript code", ["java", "javascript"])
    assert "javascript" in terms
    assert "java" not in terms


def test_extract_experience_signals_finds_years_and_level():
    signals = extract_experience_signals(SAMPLE_RESUME)
    assert signals["years_experience"] == 4.0
    assert signals["estimated_level"] == "senior"  # 4 years crosses the senior threshold


def test_extract_experience_signals_defaults_to_mid_with_no_signal():
    signals = extract_experience_signals("I build things with computers.")
    assert signals["years_experience"] is None
    assert signals["estimated_level"] == "mid"


def test_parse_resume_txt_end_to_end():
    result = parse_resume("resume.txt", SAMPLE_RESUME.encode("utf-8"))
    assert "python" in result["extracted_technologies"]
    assert "fastapi" in result["extracted_technologies"]
    assert result["experience_signals"]["years_experience"] == 4.0


def test_parse_resume_rejects_empty_text():
    import pytest

    with pytest.raises(ValueError):
        parse_resume("empty.txt", b"   ")
