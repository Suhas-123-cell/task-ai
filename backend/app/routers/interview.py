"""Interview lifecycle: start a session, fetch current question, submit answers."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.database import get_db
from app.models.db_models import Candidate, InterviewSession
from app.schemas.schemas import (
    AnswerSubmitRequest,
    AnswerSubmitResponse,
    QuestionOut,
    SessionCreateRequest,
    SessionOut,
    SessionStartResponse,
)
from app.services import interview_engine

router = APIRouter(prefix="/api/interview", tags=["interview"])


def _get_session_or_404(db: DBSession, session_id: int) -> InterviewSession:
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    return session


@router.post("/sessions", response_model=SessionStartResponse, status_code=201)
def create_session(payload: SessionCreateRequest, db: DBSession = Depends(get_db)) -> SessionStartResponse:
    candidate = db.get(Candidate, payload.candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    session, question = interview_engine.start_session(db, candidate)
    return SessionStartResponse(session=SessionOut.model_validate(session), question=QuestionOut.model_validate(question))


@router.get("/sessions/{session_id}", response_model=SessionOut)
def get_session(session_id: int, db: DBSession = Depends(get_db)) -> InterviewSession:
    return _get_session_or_404(db, session_id)


@router.get("/sessions/{session_id}/current-question", response_model=QuestionOut)
def get_current_question(session_id: int, db: DBSession = Depends(get_db)):
    session = _get_session_or_404(db, session_id)
    if session.status == "completed":
        raise HTTPException(status_code=409, detail="Session already completed; fetch the report instead")
    unanswered = [q for q in session.questions if q.answer is None]
    if not unanswered:
        raise HTTPException(status_code=404, detail="No current question found for this session")
    return unanswered[-1]


@router.post("/sessions/{session_id}/answer", response_model=AnswerSubmitResponse)
def submit_answer(
    session_id: int, payload: AnswerSubmitRequest, db: DBSession = Depends(get_db)
) -> AnswerSubmitResponse:
    session = _get_session_or_404(db, session_id)
    if session.status == "completed":
        raise HTTPException(status_code=409, detail="This interview session is already completed")

    unanswered = [q for q in session.questions if q.answer is None]
    if not unanswered:
        raise HTTPException(status_code=409, detail="No pending question awaiting an answer")
    current_question = unanswered[-1]

    answer, next_question, is_complete = interview_engine.submit_answer(
        db, session, current_question, payload.answer_text
    )

    return AnswerSubmitResponse(
        session=SessionOut.model_validate(session),
        evaluated_answer=answer,
        next_question=QuestionOut.model_validate(next_question) if next_question else None,
        is_complete=is_complete,
    )
