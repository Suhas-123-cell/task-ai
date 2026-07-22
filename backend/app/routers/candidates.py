"""Candidate entry: role listing, resume upload and parsing."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session as DBSession

from app.database import get_db
from app.models.db_models import Candidate
from app.schemas.schemas import CandidateOut, RoleInfo
from app.services.resume_parser import extract_matched_terms, parse_resume
from app.services.skills_taxonomy import ROLE_SKILL_FOCUS

router = APIRouter(prefix="/api", tags=["candidates"])

ROLES: dict[str, RoleInfo] = {
    "ai_ml_engineer": RoleInfo(
        slug="ai_ml_engineer",
        display_name="AI / ML Engineer",
        description="Concept learning, classical ML, neural networks, and RL fundamentals.",
    ),
    "backend_engineer": RoleInfo(
        slug="backend_engineer",
        display_name="Backend Engineer",
        description="API design, databases, caching, concurrency, system design, and security.",
    ),
    "data_scientist": RoleInfo(
        slug="data_scientist",
        display_name="Data Scientist",
        description="Statistics, EDA, feature engineering, model evaluation, and experimentation.",
    ),
}

MAX_RESUME_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = (".pdf", ".txt")


@router.get("/roles", response_model=list[RoleInfo])
def list_roles() -> list[RoleInfo]:
    return list(ROLES.values())


@router.post("/candidates", response_model=CandidateOut, status_code=201)
async def upload_candidate(
    target_role: str = Form(...),
    full_name: str = Form("Candidate"),
    resume: UploadFile = File(...),
    db: DBSession = Depends(get_db),
) -> Candidate:
    if target_role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Unknown role '{target_role}'. Valid roles: {list(ROLES)}")

    if not resume.filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400, detail=f"Resume must be one of: {ALLOWED_EXTENSIONS}")

    file_bytes = await resume.read()
    if len(file_bytes) > MAX_RESUME_BYTES:
        raise HTTPException(status_code=400, detail="Resume file exceeds 5MB limit")
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded resume file is empty")

    try:
        parsed = parse_resume(resume.filename, file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    role_focused_skills = extract_matched_terms(parsed["resume_text"], ROLE_SKILL_FOCUS.get(target_role, []))

    candidate = Candidate(
        full_name=full_name.strip() or "Candidate",
        target_role=target_role,
        resume_filename=resume.filename,
        resume_text=parsed["resume_text"],
        extracted_skills=role_focused_skills,
        extracted_technologies=parsed["extracted_technologies"],
        experience_signals=parsed["experience_signals"],
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


@router.get("/candidates/{candidate_id}", response_model=CandidateOut)
def get_candidate(candidate_id: int, db: DBSession = Depends(get_db)) -> Candidate:
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate
