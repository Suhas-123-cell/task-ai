"""Final output: structured session summary and per-question traceability."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.database import get_db
from app.models.db_models import InterviewSession
from app.schemas.schemas import AnswerOut, QAPair, QuestionOut, ReportOut

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{session_id}", response_model=ReportOut)
def get_report(session_id: int, db: DBSession = Depends(get_db)) -> ReportOut:
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    if not session.report:
        raise HTTPException(
            status_code=409,
            detail="Report not yet available; the interview session is still in progress",
        )

    qa_pairs = [
        QAPair(
            question=QuestionOut.model_validate(q),
            answer=AnswerOut.model_validate(q.answer) if q.answer else None,
        )
        for q in session.questions
    ]

    report = session.report
    return ReportOut(
        session_id=session.id,
        overall_score=report.overall_score,
        summary_text=report.summary_text,
        topic_breakdown=report.topic_breakdown,
        strengths=report.strengths,
        improvement_areas=report.improvement_areas,
        qa_pairs=qa_pairs,
        created_at=report.created_at,
    )
