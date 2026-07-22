"""
Context construction: turn (role, resume signals, interview history) into a
retrieval query and a topic-selection decision.

This is the piece that makes retrieval "dynamic" rather than static per
role (assignment section 3, "Context Construction" and 7.2, "construct
queries dynamically based on resume content and role selection"): the
first question's query is seeded from the candidate's strongest declared
skills for the target role, and every subsequent query is chosen to
either go deeper on a topic the candidate answered weakly (adaptive
follow-up) or move to a fresh, not-yet-covered skill (breadth), which is
also what keeps five questions from drifting into repeats of the same
concept.
"""
from app.services.skills_taxonomy import ROLE_SKILL_FOCUS

_WEAK_SCORE_THRESHOLD = 3.0  # out of 5; below this, we probe the same topic again


def _candidate_role_skills(role: str, extracted_technologies: list[str]) -> list[str]:
    """Intersect what the candidate actually has with what matters for this role."""
    role_vocab = {s.lower() for s in ROLE_SKILL_FOCUS.get(role, [])}
    matched = [t for t in extracted_technologies if t.lower() in role_vocab]
    return matched or extracted_technologies  # fall back to whatever was found at all


def opening_query(role: str, extracted_technologies: list[str], experience_level: str) -> tuple[str, str]:
    """
    Build the first retrieval query. Returns (query, topic_hint).

    The query is focused on a single skill (the candidate's top role-relevant match),
    not a blend of several. An earlier version joined the top 3 matched skills into one
    query string (e.g. "...caching, ci/cd, docker..."), which measurably hurt retrieval
    precision: the embedding for a multi-skill query often ranked a chunk about a
    *different* one of those skills above the one actually named as the topic, which
    then looked incoherent downstream (a question labeled "caching" quoting a snippet
    about CI/CD). Retrieval precision matters more here than surfacing every matched
    skill in one query -- the full skill list is still passed to the LLM prompt
    separately via `matched_skills`, so nothing is lost by narrowing the query itself.
    """
    role_skills = _candidate_role_skills(role, extracted_technologies)
    role_label = role.replace("_", " ")

    if role_skills:
        topic_hint = role_skills[0]
        query = (
            f"{role_label} interview question testing conceptual and applied understanding of "
            f"{topic_hint}, appropriate for a {experience_level}-level candidate"
        )
    else:
        topic_hint = role_label
        query = (
            f"foundational {role_label} interview question appropriate for a "
            f"{experience_level}-level candidate"
        )
    return query, topic_hint


def next_query(
    role: str,
    extracted_technologies: list[str],
    experience_level: str,
    covered_topics: list[str],
    last_topic: str | None,
    last_score: float | None,
) -> tuple[str, str]:
    """
    Build the retrieval query for question N+1 given interview history so far.
    Adaptive rule: a weak previous answer (score < 3/5) re-probes the same
    topic at a more fundamental level; a strong or absent previous answer
    moves on to a fresh topic for breadth.
    """
    role_label = role.replace("_", " ")

    if last_topic and last_score is not None and last_score < _WEAK_SCORE_THRESHOLD:
        query = (
            f"{role_label} interview question re-explaining and probing the fundamentals of "
            f"{last_topic}, at a more basic level, for a candidate who struggled with this topic"
        )
        return query, last_topic

    role_skills = _candidate_role_skills(role, extracted_technologies)
    covered_lower = {c.lower() for c in covered_topics}
    remaining = [s for s in role_skills if s.lower() not in covered_lower]
    if remaining:
        topic_hint = remaining[0]
    else:
        topic_hint = f"{role_label} advanced topic beyond {', '.join(covered_topics) or 'prior questions'}"

    difficulty_hint = "advanced" if experience_level == "senior" and last_score and last_score >= 4 else experience_level
    query = (
        f"{role_label} interview question testing conceptual and applied understanding of "
        f"{topic_hint}, appropriate for a {difficulty_hint}-level candidate, "
        f"distinct from previously covered topics: {', '.join(covered_topics) or 'none yet'}"
    )
    return query, topic_hint
