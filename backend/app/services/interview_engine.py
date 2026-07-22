"""
Interview session orchestrator.

This is the single place that ties the pipeline together end to end:
Context Construction (query_builder) -> Knowledge Retrieval (rag_pipeline)
-> Question Generation (question_generator) -> Storage (SQLAlchemy models),
matching the "Context -> Question -> Answer -> Storage" structure the
assignment asks for in section 7.5. Routers call only this module for
interview-lifecycle logic; they never talk to rag_pipeline/question_generator
directly, which keeps the FastAPI layer a thin transport/validation shell
around the actual business logic (assignment section 4/5's separation-of-
concerns requirement).
"""
from sqlalchemy.orm import Session as DBSession

from app.config import get_settings
from app.models.db_models import Answer, Candidate, InterviewSession, Question
from app.services import query_builder
from app.services.question_generator import evaluate_answer, generate_question
from app.services.rag_pipeline import retrieve
from app.services.report_generator import build_report

settings = get_settings()


def _covered_topics(session: InterviewSession) -> list[str]:
    return [q.topic for q in session.questions]


def _last_question_and_score(session: InterviewSession) -> tuple[Question | None, float | None]:
    if not session.questions:
        return None, None
    last_q = session.questions[-1]
    score = last_q.answer.score if last_q.answer else None
    return last_q, score


def _experience_level(candidate: Candidate) -> str:
    return candidate.experience_signals.get("estimated_level", "mid")


def _create_question_for_session(db: DBSession, session: InterviewSession, candidate: Candidate) -> Question:
    experience_level = _experience_level(candidate)
    covered = _covered_topics(session)
    last_q, last_score = _last_question_and_score(session)

    if last_q is None:
        query, topic_hint = query_builder.opening_query(
            session.role, candidate.extracted_technologies, experience_level
        )
        previous_qa = None
    else:
        query, topic_hint = query_builder.next_query(
            session.role,
            candidate.extracted_technologies,
            experience_level,
            covered,
            last_q.topic,
            last_score,
        )
        previous_qa = {
            "question_text": last_q.question_text,
            "answer_text": last_q.answer.answer_text if last_q.answer else "",
            "score": last_score,
        }

    retrieved_chunks = retrieve(session.role, query, top_k=settings.retrieval_top_k)

    generated = generate_question(
        role=session.role,
        topic_hint=topic_hint,
        retrieved_chunks=retrieved_chunks,
        experience_level=experience_level,
        matched_skills=candidate.extracted_technologies,
        previous_qa=previous_qa,
    )

    question = Question(
        session_id=session.id,
        index_in_session=session.current_index,
        topic=generated.get("topic", topic_hint),
        difficulty=generated.get("difficulty", experience_level),
        question_text=generated["question"],
        retrieval_query=query,
        retrieved_context=retrieved_chunks,
    )
    db.add(question)
    db.flush()
    return question


def start_session(db: DBSession, candidate: Candidate) -> tuple[InterviewSession, Question]:
    session = InterviewSession(
        candidate_id=candidate.id,
        role=candidate.target_role,
        max_questions=settings.max_interview_questions,
        current_index=0,
    )
    db.add(session)
    db.flush()

    question = _create_question_for_session(db, session, candidate)
    db.commit()
    db.refresh(session)
    return session, question


def submit_answer(
    db: DBSession, session: InterviewSession, question: Question, answer_text: str
) -> tuple[Answer, Question | None, bool]:
    retrieved_chunks = question.retrieved_context
    evaluation = evaluate_answer(
        question_text=question.question_text, retrieved_chunks=retrieved_chunks, answer_text=answer_text
    )

    answer = Answer(
        question_id=question.id,
        answer_text=answer_text,
        score=evaluation["score"],
        feedback=evaluation["feedback"],
    )
    db.add(answer)
    session.current_index += 1
    db.flush()
    db.refresh(session)

    is_complete = session.current_index >= session.max_questions
    next_question = None

    if is_complete:
        session.status = "completed"
        from datetime import datetime, timezone

        session.completed_at = datetime.now(timezone.utc)
        db.flush()
        build_report(db, session)
    else:
        candidate = db.get(Candidate, session.candidate_id)
        next_question = _create_question_for_session(db, session, candidate)

    db.commit()
    db.refresh(session)
    db.refresh(answer)
    return answer, next_question, is_complete
