# AI-Powered Role-Based Candidate Screening System

A structured technical interview system that dynamically generates interview
questions from a candidate's resume, a chosen job role, and a
Retrieval-Augmented Generation (RAG) pipeline over a role-specific knowledge
base — rather than a static, predefined question bank.

Built for the PGAGI AI/ML & Backend Engineering Intern assignment.

> **Demo video:** see [DEMO.md](DEMO.md) for the recording checklist and the
> video link placeholder (mandatory deliverable, not yet attached).

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

Run the test suite: `pytest tests/ -v` (18 tests, all passing against the
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

## Using the assigned textbook PDFs

The assignment names specific reference books per role as the intended
primary RAG source. Two of the assignment's linked PDFs are genuinely,
officially free (author/publisher-sanctioned), and are included directly in
this repo alongside the original-written articles:

- `backend/knowledge_base/ai_ml_engineer/machine_learning_mitchell.pdf` --
  Tom Mitchell's *Machine Learning*, hosted on his own CMU faculty page
  (`cs.cmu.edu/~tom/`). 421 pages, verified to extract real chapter text
  (e.g. Concept Learning, Bayesian Learning -- matching this repo's own
  article topics).
- `backend/knowledge_base/ai_ml_engineer/pattern_recognition_bishop.pdf` --
  Christopher Bishop's *Pattern Recognition and Machine Learning*, hosted
  officially by Microsoft Research (`microsoft.com/en-us/research/`). 758
  pages, verified to extract real content.

Both are ingested automatically alongside the `.md` articles in the same
folder (adding a PDF only ever *adds* coverage, never replaces anything).

**The assignment's other 5 linked PDFs were deliberately NOT committed to
git.** Inspecting the actual URLs (every one carries a `?utm_source=chatgpt.com`
suffix, suggesting they were surfaced by an AI web search rather than
vetted by hand) shows they point to what appear to be unauthorized mirrors
of commercially-sold books -- a well-known piracy aggregator (PDFDrive), a
copy with `z-lib.org` literally in its filename, and other obscure
third-party mirror sites, none of them the author's or publisher's own
official distribution. Redistributing those via a public git repository
would mean hosting infringing copies of commercial books, which this
project does not do regardless of the assignment's own sourcing or who is
requesting it.

They are present **locally only** (used to enrich local RAG demoing) and
explicitly excluded in `.gitignore` -- they exist on the machine this was
developed on but were never `git add`ed, committed, or pushed, and cloning
this repository will not include them:

| Book | Role | Local filename (gitignored) |
|---|---|---|
| Burkov, *The Hundred-Page ML Book* | ai_ml_engineer | `burkov_hundred_page_ml_book.pdf` |
| *Machine Learning for Absolute Beginners* | ai_ml_engineer | `ml_for_absolute_beginners.pdf` |
| *AI, Machine Learning & Deep Learning* | ai_ml_engineer | `ai_ml_deep_learning_overview.pdf` |
| Muller & Guido, *Intro to ML with Python* | data_scientist | `intro_to_ml_with_python.pdf` |
| Brownlee, *Master ML Algorithms* | data_scientist | `master_ml_algorithms_brownlee.pdf` |

If you want these in your own local copy of this repo, you'd need to source
them yourself through a channel you're comfortable with (purchasing the
book, a library, etc.) and drop them into the paths above -- re-running
ingestion (below) picks them up the same way it would any other PDF.

To add any additional PDF (from a source you've verified yourself) for any
role:

1. Drop the PDF file directly into that role's knowledge base folder --
   no renaming or preprocessing needed, e.g.:
   ```
   backend/knowledge_base/data_scientist/intro_to_ml_with_python.pdf
   ```
2. Re-run ingestion for that role (or all roles):
   ```bash
   cd backend
   source .venv/bin/activate
   python scripts/ingest_kb.py ai_ml_engineer   # a single role
   python scripts/ingest_kb.py                  # or all roles
   ```
3. Restart the backend (`uvicorn app.main:app --reload`) so it picks up the
   updated Chroma collection.

**Caveats to expect with full textbooks, not article-length content:**
- A full book will produce many more chunks than the existing articles and
  take noticeably longer to embed on first ingestion (still a one-time cost,
  not a per-request one).
- `pypdf` text extraction from real scanned/typeset academic PDFs is not
  always clean -- page headers/footers, footnotes, and OCR artifacts can end
  up as stray sentences. The semantic chunker (see below) is reasonably
  robust to this since it groups by sentence-embedding similarity rather than
  raw structure, but chunk quality from a real textbook will vary more than
  from the hand-written articles included here.
- If ingestion is skipped entirely for a role after a fresh clone, the
  backend now fails loudly rather than silently degrading -- see "Known
  limitations" below.

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

**Why the knowledge base is mostly original writing, with two real textbooks
added where a legitimate source existed.** The assignment names specific
textbooks as the intended source, but most of its own linked PDFs turned out
to be unauthorized mirrors of commercially-sold books (see "Using the
assigned textbook PDFs" above) -- redistributing those via a public repo
was not something this project would do regardless of the assignment's own
sourcing. `backend/knowledge_base/` contains 22 original technical articles
(8 for AI/ML Engineer mirroring Mitchell's table of contents -- concept
learning, decision trees, neural networks, Bayesian learning, instance-based
learning, computational learning theory, reinforcement learning, hypothesis
evaluation; 8 for Backend Engineer; 6 for Data Scientist) at comparable
technical depth, **plus** the full text of Mitchell's *Machine Learning* and
Bishop's *Pattern Recognition and Machine Learning* -- both fetched from
their author/publisher's own official free hosting, not a mirror -- in
`ai_ml_engineer`. The ingestion pipeline is format-agnostic (`.md`, `.txt`,
and `.pdf` are all supported in `load_role_documents`), so any additional
legitimately-sourced PDF can be dropped into the same directories and picked
up by re-running `scripts/ingest_kb.py` with zero code changes.

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
- **Ingestion is a required manual step after a fresh clone.** A role whose
  Chroma collection has never been ingested (e.g. `scripts/ingest_kb.py` was
  never run) now fails loudly with a 503 and an actionable message
  (`KnowledgeBaseNotIngestedError` in `rag_pipeline.py`) rather than silently
  falling back to context-free question generation -- previously, a skipped
  ingestion step was indistinguishable from a normal (if low-relevance)
  retrieval. There is no automatic ingest-on-first-request fallback by
  design: ingestion is a deliberate, explicit setup step (see Setup above),
  not something that should happen implicitly inside a request handler.

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
