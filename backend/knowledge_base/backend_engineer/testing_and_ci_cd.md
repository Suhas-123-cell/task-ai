# Testing Strategy and CI/CD

The test pyramid describes a healthy balance of test types: many fast,
narrow unit tests at the base (testing a single function or class in
isolation, with dependencies mocked or stubbed), fewer integration tests
in the middle (testing that multiple components -- e.g. a service plus a
real test database -- work together correctly), and a small number of
end-to-end tests at the top (exercising the full stack through its real
interfaces, closest to what a user actually experiences, but slowest and
most brittle). Inverting the pyramid (mostly slow E2E tests, few unit
tests) is a common anti-pattern: the test suite becomes slow, flaky, and
hard to debug, because a single failure could originate anywhere in a
long call chain.

Unit tests should be deterministic and isolated from external state:
a test that calls a real LLM API, hits a real network, or depends on the
current date will be flaky (fails intermittently for reasons unrelated to
a real bug) or slow. Dependency injection -- passing collaborators into a
function/class rather than constructing them internally -- is what makes
a component testable in isolation, since a test can inject a fake or mock
collaborator instead of the real one; this is exactly why FastAPI's
dependency-injection system (the `Depends` mechanism) is valuable beyond
convenience: it lets tests override a real database session with an
in-memory/test one without touching route handler code.

Integration tests for a backend commonly spin up a real (but ephemeral,
e.g. an on-disk SQLite file created fresh per test run) database rather
than mocking the ORM, because the ORM/database interaction (migrations,
constraints, query correctness) is often exactly what needs verifying,
and mocking it away would test nothing meaningful about that interaction.

Continuous Integration (CI) runs the test suite (plus linting, type
checking, security scanning) automatically on every commit or pull
request, catching regressions before they reach a shared branch.
Continuous Deployment/Delivery (CD) automates promoting a change that
passes CI through environments (staging, then production), ideally with a
rollback path (reverting to the previous known-good build/version) that
is at least as automated as the forward deployment, since a fast, safe
rollback is often more valuable during an incident than a fast forward
deploy.

A key discipline that ties testing and CI/CD together is treating a
failing test as a blocking signal, not a suggestion: a CI pipeline that
allows merges despite red tests, or a team that habitually skips/deletes
flaky tests instead of fixing their root cause, gradually loses the
entire value of having a test suite, because "green" stops meaning
"safe."
