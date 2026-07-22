"""
Unit tests for adaptive query/topic construction -- in particular a
regression test for the topic-coverage bug found during manual testing:
next_query() must advance to a new topic on a strong answer instead of
being stuck on whatever the first matched skill was.
"""
from app.services.query_builder import next_query, opening_query

CANDIDATE_SKILLS = ["caching", "docker", "fastapi", "postgresql"]


def test_opening_query_picks_top_role_relevant_skill():
    query, topic_hint = opening_query("backend_engineer", CANDIDATE_SKILLS, "mid")
    assert topic_hint == "caching"  # first in the (alphabetically pre-sorted) candidate skill list
    assert "backend engineer" in query
    assert "mid-level" in query


def test_next_query_advances_topic_on_strong_answer():
    # Regression test: previously, if the caller passed back a topic label that didn't
    # exactly match a role-skill token (e.g. re-derived from a retrieved chunk's filename
    # instead of the original topic_hint), `remaining` never shrank and the same topic
    # kept getting selected question after question. Simulate three strong answers and
    # assert the topic actually advances each time using the topic values next_query itself
    # returned (mirroring how interview_engine feeds covered_topics back in).
    covered = []
    last_topic = None
    last_score = None
    seen_topics = []

    for _ in range(3):
        _, topic_hint = next_query("backend_engineer", CANDIDATE_SKILLS, "mid", covered, last_topic, last_score)
        seen_topics.append(topic_hint)
        covered.append(topic_hint)
        last_topic, last_score = topic_hint, 5.0  # simulate a strong answer each time

    assert len(set(seen_topics)) == len(seen_topics), f"topics did not advance: {seen_topics}"


def test_next_query_reprobes_same_topic_on_weak_answer():
    query, topic_hint = next_query("backend_engineer", CANDIDATE_SKILLS, "mid", ["caching"], "caching", 2.0)
    assert topic_hint == "caching"
    assert "fundamentals" in query
