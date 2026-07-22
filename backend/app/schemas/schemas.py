"""Pydantic request/response contracts exposed by the API layer."""
from datetime import datetime

from pydantic import BaseModel, Field


# ---------- Candidates ----------

class CandidateOut(BaseModel):
    id: int
    full_name: str
    target_role: str
    extracted_skills: list[str]
    extracted_technologies: list[str]
    experience_signals: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleInfo(BaseModel):
    slug: str
    display_name: str
    description: str


# ---------- Interview lifecycle ----------

class SessionCreateRequest(BaseModel):
    candidate_id: int


class QuestionOut(BaseModel):
    id: int
    index_in_session: int
    topic: str
    difficulty: str
    question_text: str
    # Traceability: which retrieval query + chunks produced this question.
    retrieval_query: str
    retrieved_context: list[dict]

    model_config = {"from_attributes": True}


class SessionOut(BaseModel):
    id: int
    candidate_id: int
    role: str
    status: str
    max_questions: int
    current_index: int
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class SessionStartResponse(BaseModel):
    session: SessionOut
    question: QuestionOut


class AnswerSubmitRequest(BaseModel):
    answer_text: str = Field(min_length=1, max_length=8000)


class AnswerSubmitResponse(BaseModel):
    session: SessionOut
    evaluated_answer: "AnswerOut"
    next_question: QuestionOut | None = None
    is_complete: bool


class AnswerOut(BaseModel):
    id: int
    question_id: int
    answer_text: str
    score: float | None
    feedback: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Reports ----------

class QAPair(BaseModel):
    question: QuestionOut
    answer: AnswerOut | None


class ReportOut(BaseModel):
    session_id: int
    overall_score: float
    summary_text: str
    topic_breakdown: list[dict]
    strengths: list[str]
    improvement_areas: list[str]
    qa_pairs: list[QAPair]
    created_at: datetime

    model_config = {"from_attributes": True}


AnswerSubmitResponse.model_rebuild()
