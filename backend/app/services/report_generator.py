"""
Final-output synthesis: turn a completed interview session's stored
Question/Answer chain into a structured summary with basic insights
(assignment section 3, "Final Output" -- "structured summary" plus
"basic insights or analysis of the session").
"""
from sqlalchemy.orm import Session as DBSession

from app.llm.groq_client import LLMUnavailableError, chat_json, is_llm_configured
from app.models.db_models import InterviewSession, Report

SUMMARY_SYSTEM_PROMPT = """You are a senior technical interviewer writing a concise, honest \
post-interview summary for a hiring team. You will be given every question asked, the \
candidate's answer to each, and a score (1-5) for each answer.

Write a short overall narrative summary (3-4 sentences) of the candidate's demonstrated \
understanding across the interview, referencing specific topics where relevant. Then list \
2-4 concrete strengths and 1-3 concrete improvement areas, each grounded in a specific \
question/answer, not generic statements.

Respond with a single JSON object: {"summary": "...", "strengths": ["...", ...], \
"improvement_areas": ["...", ...]}"""


def _fallback_summary(topic_scores: list[dict], overall_score: float) -> dict:
    strengths = [t["topic"] for t in topic_scores if t["average_score"] >= 4.0]
    improvement_areas = [t["topic"] for t in topic_scores if t["average_score"] < 3.0]
    summary = (
        f"The candidate completed {len(topic_scores)} question(s) with an average score of "
        f"{overall_score:.1f}/5. "
        + (f"Stronger performance was shown on: {', '.join(strengths)}. " if strengths else "")
        + (f"Weaker performance was shown on: {', '.join(improvement_areas)}. " if improvement_areas else "")
        + "(Automated fallback summary -- configure GROQ_API_KEY for a qualitative narrative.)"
    )
    return {"summary": summary, "strengths": strengths or ["Not enough signal to determine"], "improvement_areas": improvement_areas or ["None identified"]}


def build_report(db: DBSession, session: InterviewSession) -> Report:
    qa_lines = []
    topic_scores_map: dict[str, list[float]] = {}

    for question in session.questions:
        score = question.answer.score if question.answer else 0.0
        topic_scores_map.setdefault(question.topic, []).append(score)
        qa_lines.append(
            f"Q{question.index_in_session + 1} [{question.topic}]: {question.question_text}\n"
            f"A: {question.answer.answer_text if question.answer else '(no answer)'}\n"
            f"Score: {score}/5"
        )

    topic_breakdown = [
        {"topic": topic, "average_score": round(sum(scores) / len(scores), 2), "questions_asked": len(scores)}
        for topic, scores in topic_scores_map.items()
    ]
    all_scores = [s for scores in topic_scores_map.values() for s in scores]
    overall_score = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0

    if is_llm_configured() and qa_lines:
        try:
            result = chat_json(
                SUMMARY_SYSTEM_PROMPT,
                f"Role: {session.role.replace('_', ' ')}\n\n" + "\n\n".join(qa_lines),
            )
            summary_text = result.get("summary", "")
            strengths = result.get("strengths", [])
            improvement_areas = result.get("improvement_areas", [])
            if not summary_text:
                raise ValueError("empty summary")
        except (LLMUnavailableError, ValueError, KeyError):
            fallback = _fallback_summary(topic_breakdown, overall_score)
            summary_text, strengths, improvement_areas = (
                fallback["summary"], fallback["strengths"], fallback["improvement_areas"]
            )
    else:
        fallback = _fallback_summary(topic_breakdown, overall_score)
        summary_text, strengths, improvement_areas = (
            fallback["summary"], fallback["strengths"], fallback["improvement_areas"]
        )

    report = Report(
        session_id=session.id,
        overall_score=overall_score,
        summary_text=summary_text,
        topic_breakdown=topic_breakdown,
        strengths=strengths,
        improvement_areas=improvement_areas,
    )
    db.add(report)
    db.flush()
    return report
