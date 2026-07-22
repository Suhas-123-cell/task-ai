# AI-Powered Role-Based Candidate Screening System

A structured technical interview system that dynamically generates interview
questions from a candidate's resume, a chosen job role, and a
Retrieval-Augmented Generation (RAG) pipeline over a role-specific knowledge
base — rather than a static, predefined question bank.

Built for the PGAGI AI/ML & Backend Engineering Intern assignment.

## Demo flow at a glance

1. Candidate uploads a resume (PDF/txt) and picks a role (AI/ML Engineer,
   Backend Engineer, or Data Scientist).
2. The backend parses the resume and extracts role-relevant skills, matched
   technologies, and a coarse experience level (junior/mid/senior).
3. A retrieval query is built from the candidate's top skill for the chosen
   role, embedded, and matched against a persistent per-role vector store.
4. An LLM (Groq, `llama-3.3-70b-versatile`) generates one interview question
   grounded in the retrieved excerpts — required to be answerable from that
   context, calibrated to the candidate's experience level.
5. The candidate answers in the UI; the answer is scored 1-5 against the same
   retrieved context, with short grounded feedback.
6. The next question adapts: a weak answer (<3/5) re-probes the same topic at
   a more basic level; a strong answer advances to a new, uncovered skill.
7. After 5 questions, a structured report is generated: overall score,
   narrative summary, strengths, improvement areas, and a per-topic score
   breakdown — plus the full traceable transcript (every question stores
   exactly which retrieval query and which chunks produced it).

## Architecture

```
+-------------+      HTTP/JSON       +--------------------------------------+
|   React UI   |<--------------------->|            FastAPI backend           |
| (Vite, JSX)  |                       |                                      |
+-------------+                       |  routers/  -> candidates, interview, |
                                       |              reports (thin, HTTP     |
                                       |              validation only)        |
                                       |  services/ -> resume_parser,         |
                                       |              rag_pipeline,           |
                                       |              query_builder,          |
                                       |              question_generator,     |
                                       |              interview_engine,       |
                                       |              report_generator        |
                                       |  llm/      -> groq_client            |
                                       |  models/   -> SQLAlchemy ORM         |
                                       +--------+---------------+------------+
                                                |               |
                                     +----------v-----+   +-----v------+
                                     |  SQLite (data/  |   |  ChromaDB  |
                                     |  app.db)        |   |  (persistent,
                                     |  sessions,      |   |  per-role  |
                                     |  questions,     |   |  collections)
                                     |  answers,       |   +------------+
                                     |  reports        |
                                     +-----------------+
```

Every layer only talks to the layer directly below it: routers call
`interview_engine` (the single orchestrator), which calls `query_builder` ->
`rag_pipeline` -> `question_generator` -> the ORM, in that order, matching the
assignment's required `Context -> Question -> Answer -> Storage` pipeline
structure. Routers never call `rag_pipeline` or `question_generator`
directly.

## Setup

### Prerequisites
- Python 3.12 (Python 3.14 does **not** currently have prebuilt wheels for
  `pydantic-core`/`tokenizers` -- use 3.12 or 3.11)
- Node.js 18+
- A free [Groq API key](https://console.groq.com) (optional -- see below)

### Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and set GROQ_API_KEY if you have one

python scripts/ingest_kb.py       # builds the vector store from knowledge_base/
uvicorn app.main:app --reload --port 8000
```

Run the test suite: `pytest tests/ -v` (15 tests, all passing against the
deterministic fallback path -- no API key needed to run tests).

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # only needed if the backend isn't on localhost:8000
npm run dev
```

Open the printed local URL (default `http://localhost:5173`).

### Without a Groq API key

The system is fully functional with `GROQ_API_KEY` left blank: question
generation and answer scoring fall back to deterministic, context-grounded
logic (a template-based question construction and a keyword-overlap scoring
heuristic). This is explicitly a **lower-quality fallback**, not the intended
primary path -- the assignment specifically warns against "generic or
template-driven outputs," which is exactly what the fallback risks being.
Configure a real key for the intended experience.

## Key design decisions

**Why SQLite, not Postgres.** Persistence is required by the assignment, but
zero external services should be needed to run this locally. `database.py`
uses only portable SQLAlchemy types, so switching `DATABASE_URL` to Postgres
later needs no other code change.

**Why a local embedding model, not a hosted embedding API.** Embeddings are
needed on both ingestion *and* every single query at interview time -- keeping
that hot path free of network latency, rate limits, and per-call cost
mattered more than the marginal quality gain of a larger hosted model.
`sentence-transformers/all-MiniLM-L6-v2` runs in-process.

**Chunking strategy: semantic, not fixed-size.** Each sentence is embedded, and a
new chunk starts exactly where cosine similarity to the next sentence drops
below a threshold (a detected topic shift), bounded by a min/max chunk size so
neither a long run of similar sentences nor a run of dissimilar short ones
produces a degenerate chunk. An earlier fixed-character-count chunker (with
sentence-boundary snapping so it at least didn't cut mid-sentence) routinely
grouped unrelated sentences together and split single ideas across two
overlapping chunks, diluting both the embedding signal and the grounding
handed to the question generator -- a form of "context rot." Semantic
chunking's boundaries align with actual topic shifts instead, and the old
overlap mechanism (which existed to avoid losing context at an arbitrary cut
point) is no longer needed once boundaries are chosen at natural breaks.

**Context-rot mitigation at retrieval time too.** Even with better chunk
boundaries, a fixed `top_k` can still force in a chunk that isn't actually
relevant just to fill the quota. `retrieve()` drops any result below
`RETRIEVAL_MIN_SIMILARITY`, returning fewer than `top_k` chunks (down to a
guaranteed minimum of one) rather than padding the LLM prompt with
low-relevance filler that dilutes attention away from what's actually useful.

**Why the knowledge base is original writing, not the linked textbook PDFs.**
The assignment names specific textbooks (Mitchell's *Machine Learning*, etc.)
as the intended source. Reliably fetching and redistributing full copyrighted
textbook PDFs within the assignment window was both unreliable and legally
murky for a public repo. Instead, `backend/knowledge_base/` contains 22
original technical articles (8 for AI/ML Engineer mirroring Mitchell's table
of contents -- concept learning, decision trees, neural networks, Bayesian
learning, instance-based learning, computational learning theory,
reinforcement learning, hypothesis evaluation; 8 for Backend Engineer; 6 for
Data Scientist) at comparable technical depth. The ingestion pipeline is
format-agnostic (`.md`, `.txt`, and `.pdf` are all supported in
`load_role_documents`) -- dropping the real textbook PDFs into the same
directories and re-running `scripts/ingest_kb.py` swaps in the actual source
material with zero code changes.

**Adaptive question flow.** `query_builder.next_query` implements the
assignment's optional-but-valued adaptivity: a previous answer scoring below
3/5 triggers a follow-up query that re-probes the *same* topic at a more
fundamental level; a score of 3+ advances to a new, not-yet-covered
role-relevant skill. This was stress-tested manually -- feeding deliberately
weak/mismatched answers correctly kept the interview re-probing the same
topic instead of advancing, and strong answers advanced through 5 distinct
topics without repeats (see `tests/test_query_builder.py` and the
topic-distinctness assertion in `tests/test_api_flow.py`).

**Traceability.** Every `Question` row stores the exact retrieval query and
the exact retrieved chunks (with source file and similarity score) that
produced it. The frontend's "Why this question?" toggle surfaces this
directly, so a reviewer can see the grounding, not just trust it.

**No router library on the frontend.** The interview is a strict, linear
three-stage wizard (upload -> interview -> summary) that never needs
deep-linking or back/forward navigation between stages. A single `stage`
variable in `App.jsx` is simpler to reason about than URL-based routing for a
flow this constrained.

## Known limitations

Found and explicitly accepted (not silently missed) during a security review
of this codebase:

- **No authentication/authorization.** Any client can view any
  candidate/session/report by guessing a sequential integer ID. Acceptable
  for this assignment's scope (no login was specified, single-user local
  demo) -- a real multi-tenant deployment would need per-candidate access
  tokens before this could hold real users' data.
- **No rate limiting.** A public deployment could have its
  `/api/interview/sessions/*/answer` endpoint hit in a loop to drive
  unbounded Groq API cost. Out of scope for a local demo; would need
  addressing before any public hosting.
- **Retrieval quality depends on knowledge-base breadth.** A topic with no
  dedicated KB article (before `containerization_and_deployment.md` was
  added, this was true for Docker/Kubernetes) falls back to whatever
  existing article is semantically closest, which can look like a topic
  mismatch. Swapping in the full source textbooks (see above) would give
  broader, deeper coverage.
- **Fallback answer scoring is a blunt heuristic** (answer length + keyword
  overlap with retrieved context), not real reasoning. It exists purely so
  the system runs end to end with zero API key configured; it will score a
  correct-but-differently-worded answer unfairly low. The real Groq-backed
  scoring path is the intended experience.

## Repository layout

```
backend/
  app/
    routers/     candidates.py, interview.py, reports.py  (HTTP layer)
    services/    resume_parser, rag_pipeline, query_builder,
                 question_generator, interview_engine, report_generator
    llm/         groq_client.py
    models/      db_models.py (SQLAlchemy ORM)
    schemas/     schemas.py (pydantic request/response contracts)
    config.py    environment-variable-driven settings
    database.py  engine/session setup
    main.py      FastAPI app, CORS, error handling, startup
  knowledge_base/  ai_ml_engineer/, backend_engineer/, data_scientist/
  scripts/ingest_kb.py   builds/rebuilds the vector store
  tests/                 pytest suite (unit + full HTTP-level integration)
frontend/
  src/
    pages/       UploadPage, InterviewPage, SummaryPage
    api/client.js
    App.jsx, main.jsx, styles/
```
