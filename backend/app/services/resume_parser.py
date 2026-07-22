"""
Resume ingestion: turn an uploaded PDF/text file into structured signal
(raw text, matched skills/technologies, coarse experience signals) that
downstream RAG query construction and question generation can condition on.
"""
import io
import re

from pypdf import PdfReader

from app.services.skills_taxonomy import ALL_TECHNOLOGIES

_YEARS_EXPERIENCE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+(?:of\s+)?experience", re.IGNORECASE
)
_SENIORITY_TERMS = ["intern", "junior", "senior", "lead", "staff", "principal", "graduate", "entry-level"]
_PROJECT_HEADER_RE = re.compile(r"^\s*(projects?|experience|work experience)\s*:?\s*$", re.IGNORECASE | re.MULTILINE)


def extract_text_from_upload(filename: str, file_bytes: bytes) -> str:
    """Extract raw text from an uploaded resume file (PDF or plain text)."""
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages)
    else:
        text = file_bytes.decode("utf-8", errors="ignore")

    text = text.strip()
    if not text:
        raise ValueError(
            "No extractable text found in the uploaded resume. "
            "If this is a scanned/image-only PDF, please upload a text-based PDF or a .txt file."
        )
    return text


def extract_matched_terms(resume_text: str, vocabulary: list[str]) -> list[str]:
    """Case-insensitive, word-boundary-safe substring match against a vocabulary list.

    Single-character terms ("c", "r") use a stricter boundary than everything else:
    ordinary alnum-only boundaries let them match inside "C++"/"C#" (the "+"/"#" count
    as a boundary) or abbreviations like "C.S."/"M.S." (the "." counts as a boundary),
    producing a spurious bare "c" match alongside the real "c++" match. Found via a
    real bug report: that stray "c" ended up quoted verbatim in a generated interview
    question. Multi-character terms keep the original (looser) boundary since they
    need it -- e.g. "node.js" must still match right up against a following period.
    """
    lowered = resume_text.lower()
    matched = []
    for term in vocabulary:
        term_lower = term.lower()
        if len(term_lower) <= 1:
            pattern = r"(?<![a-z0-9+#.])" + re.escape(term_lower) + r"(?![a-z0-9+#.])"
        else:
            pattern = r"(?<![a-z0-9])" + re.escape(term_lower) + r"(?![a-z0-9])"
        if re.search(pattern, lowered):
            matched.append(term)
    return matched


def extract_experience_signals(resume_text: str) -> dict:
    """Coarse heuristics used to bias question difficulty (assignment 7.4)."""
    years_matches = [float(m.group(1)) for m in _YEARS_EXPERIENCE_RE.finditer(resume_text)]
    max_years = max(years_matches) if years_matches else None

    lowered = resume_text.lower()
    seniority_hits = [term for term in _SENIORITY_TERMS if term in lowered]
    project_sections = len(_PROJECT_HEADER_RE.findall(resume_text))

    if max_years is not None:
        level = "senior" if max_years >= 4 else ("mid" if max_years >= 1.5 else "junior")
    elif "senior" in seniority_hits or "lead" in seniority_hits or "principal" in seniority_hits:
        level = "senior"
    elif "intern" in seniority_hits or "entry-level" in seniority_hits or "graduate" in seniority_hits:
        level = "junior"
    else:
        level = "mid"

    return {
        "years_experience": max_years,
        "seniority_terms_found": seniority_hits,
        "project_sections_detected": project_sections,
        "estimated_level": level,
    }


def parse_resume(filename: str, file_bytes: bytes) -> dict:
    """Full parse pipeline: text -> {text, skills, technologies, experience_signals}."""
    text = extract_text_from_upload(filename, file_bytes)
    technologies = extract_matched_terms(text, ALL_TECHNOLOGIES)
    return {
        "resume_text": text,
        "extracted_technologies": technologies,
        "experience_signals": extract_experience_signals(text),
    }
