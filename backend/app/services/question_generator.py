"""
Question generation and answer evaluation grounded in retrieved context.

Assignment 7.3 explicitly warns against "generic or template-driven
outputs." The primary path here is an LLM call (Groq) whose prompt forces
the model to justify each question against the specific retrieved chunks
it was given, rather than free-associating from its own training data --
this is what makes the output "RAG" rather than just "ask an LLM for
interview questions." A deterministic fallback exists so the system still
functions end-to-end with zero API key configured (e.g. for grading or
offline demoing), but it is explicitly a lower-quality fallback, not the
intended primary path.
"""
from app.llm.groq_client import LLMUnavailableError, chat_json, is_llm_configured

QUESTION_SYSTEM_PROMPT = """You are a senior technical interviewer conducting a structured \
screening interview. You will be given: the target role, signals extracted from the \
candidate's resume, one or more excerpts retrieved from a role-specific reference corpus, \
a topic to focus on, and (optionally) the previous question/answer/score in this interview.

Generate exactly ONE new interview question. Requirements:
- The question MUST be answerable using concepts present in the retrieved excerpts -- do not \
invent facts or ask about anything outside them.
- The question must NOT be a generic, memorized-sounding interview question ("what is X?"); \
it should require the candidate to reason, compare, or apply a concept from the excerpts.
- Calibrate difficulty to the candidate's experience level and, if a previous score is given, \
adapt: if the previous score was low, ask a more foundational question on the same topic; if \
high, go deeper or move to a new topic.
- Do not repeat the previous question's topic unless you are deliberately probing a weak answer.

Respond with a single JSON object: {"question": "...", "topic": "short topic label", \
"difficulty": "junior"|"mid"|"senior"}"""

EVAL_SYSTEM_PROMPT = """You are a senior technical interviewer grading a candidate's spoken \
answer to an interview question. You will be given the question, the reference excerpts the \
question was grounded in, and the candidate's answer.

Score the answer from 1 (incorrect or no understanding shown) to 5 (thorough, accurate, and \
applies the concept correctly, matching or exceeding what the reference excerpts describe). \
Give brief, specific feedback (max 2 sentences) that references what was right or missing, \
grounded in the reference excerpts -- not generic praise or criticism.

Respond with a single JSON object: {"score": <number 1-5>, "feedback": "..."}"""


def _format_context(retrieved_chunks: list[dict]) -> str:
    lines = []
    for i, chunk in enumerate(retrieved_chunks, start=1):
        lines.append(f"[Excerpt {i} - from {chunk['source_file']}]\n{chunk['text']}")
    return "\n\n".join(lines)


def _topic_label_from_source(source_file: str) -> str:
    """Derive a human-readable label from a KB filename, e.g. 'api_design.md' -> 'Api Design'."""
    return source_file.rsplit(".", 1)[0].replace("_", " ").title()


def _fallback_question(topic_hint: str, retrieved_chunks: list[dict], experience_level: str) -> dict:
    """
    Deterministic, context-grounded (but template-based) question when no LLM key is set.

    The returned "topic" is always `topic_hint`, never re-derived from whichever chunk the
    retriever ranked first. `topic_hint` is the skill-level unit query_builder uses to track
    which topics have already been covered across the interview (see next_query's
    covered_topics handling). Relabeling it from retrieved content silently breaks that
    tracking -- confirmed during manual testing: the retriever kept ranking the same KB
    article highest for several different topic_hints in the backend_engineer role, and
    deriving "topic" from that article's filename made every question look like the same
    topic, so the interview never advanced past it. The chunk's own source file is still
    used below to select which text to quote, since a quote must match its own source.
    """
    if retrieved_chunks:
        top_chunk = retrieved_chunks[0]
        sentences = [s.strip() for s in top_chunk["text"].strip().split(". ") if len(s.strip()) > 30]
        snippet = (sentences[-1] if sentences else top_chunk["text"].strip())[:220].rstrip(".") + "."
        source_label = _topic_label_from_source(top_chunk["source_file"])
        question = (
            f'Based on the following idea from our {source_label} material -- "{snippet}" -- '
            f"explain how this relates to {topic_hint}, in your own words, and describe a "
            f"situation where it would matter in practice."
        )
    else:
        question = f"Describe your practical experience with {topic_hint} and a challenge you faced applying it."

    return {"question": question, "topic": topic_hint, "difficulty": experience_level}


def generate_question(
    *,
    role: str,
    topic_hint: str,
    retrieved_chunks: list[dict],
    experience_level: str,
    matched_skills: list[str],
    previous_qa: dict | None = None,
) -> dict:
    if not is_llm_configured():
        return _fallback_question(topic_hint, retrieved_chunks, experience_level)

    context_block = _format_context(retrieved_chunks)
    prev_block = ""
    if previous_qa:
        prev_block = (
            f"\n\nPrevious question: {previous_qa['question_text']}\n"
            f"Previous answer: {previous_qa['answer_text']}\n"
            f"Previous score (out of 5): {previous_qa.get('score', 'n/a')}"
        )

    user_prompt = (
        f"Target role: {role.replace('_', ' ')}\n"
        f"Candidate experience level: {experience_level}\n"
        f"Candidate's relevant skills from resume: {', '.join(matched_skills) or 'none extracted'}\n"
        f"Focus topic for this question: {topic_hint}\n\n"
        f"Retrieved reference excerpts:\n{context_block}"
        f"{prev_block}"
    )

    try:
        result = chat_json(QUESTION_SYSTEM_PROMPT, user_prompt)
        if not result.get("question"):
            raise ValueError("LLM returned empty question")
        # Force topic back to topic_hint rather than trusting the model's own label: the
        # adaptive/coverage logic in query_builder keys off topic_hint, so an LLM-invented
        # label here would silently break topic-coverage tracking the same way the
        # fallback path's bug did (see _fallback_question's docstring for that failure mode).
        result["topic"] = topic_hint
        result.setdefault("difficulty", experience_level)
        return result
    except (LLMUnavailableError, ValueError, KeyError):
        return _fallback_question(topic_hint, retrieved_chunks, experience_level)


def _fallback_evaluation(answer_text: str, retrieved_chunks: list[dict]) -> dict:
    """Heuristic keyword-overlap scoring when no LLM key is set."""
    answer_lower = answer_text.lower()
    context_words = set()
    for chunk in retrieved_chunks:
        context_words.update(w.strip(".,()-") for w in chunk["text"].lower().split() if len(w) > 5)

    answer_words = set(w.strip(".,()-") for w in answer_lower.split() if len(w) > 5)
    overlap = len(answer_words & context_words)

    length_score = min(len(answer_text.split()) / 40, 1.0) * 2.5
    overlap_score = min(overlap / 8, 1.0) * 2.5
    score = round(max(1.0, min(5.0, length_score + overlap_score)), 1)

    feedback = (
        "Automated fallback scoring (no LLM configured): based on answer length and overlap "
        "with reference terminology. Configure GROQ_API_KEY for qualitative, reasoning-aware feedback."
    )
    return {"score": score, "feedback": feedback}


def evaluate_answer(*, question_text: str, retrieved_chunks: list[dict], answer_text: str) -> dict:
    if not is_llm_configured():
        return _fallback_evaluation(answer_text, retrieved_chunks)

    context_block = _format_context(retrieved_chunks)
    user_prompt = (
        f"Question: {question_text}\n\nReference excerpts:\n{context_block}\n\n"
        f"Candidate's answer: {answer_text}"
    )

    try:
        result = chat_json(EVAL_SYSTEM_PROMPT, user_prompt)
        score = float(result.get("score", 3.0))
        score = max(1.0, min(5.0, score))
        feedback = result.get("feedback") or "No feedback generated."
        return {"score": round(score, 1), "feedback": feedback}
    except (LLMUnavailableError, ValueError, TypeError):
        return _fallback_evaluation(answer_text, retrieved_chunks)
