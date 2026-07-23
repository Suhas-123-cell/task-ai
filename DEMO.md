# Demo Video

## Video link

> **⚠ Not yet attached.** A demo video is a mandatory deliverable per the
> assignment. This section is a placeholder -- replace it with the actual
> link (or embed the file) before final submission:
>
> **Demo video URL: `<ADD LINK HERE BEFORE SUBMISSION>`**

## Recording checklist / script

A suggested walkthrough (~3-5 minutes) covering everything the assignment
asks the video to demonstrate: complete system flow, key features, and how
the components interact.

1. **Setup context (10-15s, optional)**
   - Briefly show the running backend (`http://localhost:8000/docs`) and
     frontend (`http://localhost:5173`) side by side, or just mention both
     are running locally.

2. **Resume upload + role selection**
   - Show the upload screen.
   - Pick a role (e.g. Backend Engineer).
   - Upload a resume (PDF or `.txt`).
   - Point out the extracted skills / experience level shown after upload,
     if visible -- this is the resume-parsing step influencing everything
     downstream.

3. **First generated question**
   - Show the generated question, its topic and difficulty badges.
   - Click **"Why this question?"** and show the retrieved knowledge-base
     excerpts and the retrieval query that produced them -- this is the
     traceability/grounding the assignment asks for (Context -> Question ->
     Answer -> Storage).
   - Briefly narrate: this question was generated from the resume's skills,
     the selected role, and retrieval over the role-specific knowledge base
     -- not a static question bank.

4. **Answering the full interview**
   - Answer the question (a real, on-topic answer works best for the demo).
   - Show the score/feedback flash.
   - Repeat through all 5 questions, pointing out at least once that the
     topic changes each time (adaptive: advances on a strong answer,
     re-probes on a weak one -- mention this even if you don't demonstrate
     the weak-answer path).

5. **Final report**
   - Show the summary page: overall score, narrative summary, strengths,
     improvement areas, and the per-topic score breakdown.
   - Scroll through the full transcript to show every question/answer/score
     is persisted, not just the final summary.

6. **Close (optional)**
   - One sentence on architecture: React frontend, FastAPI backend, RAG over
     a per-role Chroma vector store, Groq LLM for question generation and
     scoring (or fallback logic if recording without a configured API key --
     mention which mode is active).

## Word-for-word narration script

Read this naturally, don't rush it -- pause and let the screen catch up
where noted. Roughly 3-4 minutes if you don't linger.

---

**[Opening, ~10s]**

> "Hi, this is my submission for the AI-powered candidate screening
> assignment. It's a system that generates technical interview questions
> dynamically -- from a candidate's resume, their target role, and a
> Retrieval-Augmented Generation pipeline over a role-specific knowledge
> base -- rather than pulling from a fixed question bank. Let me walk
> through it."

**[Resume upload + role selection, ~20s]** *(show the upload screen)*

> "First, the candidate uploads their resume -- PDF or plain text -- and
> picks a target role. I'll pick [Backend Engineer / AI-ML Engineer / Data
> Scientist] and upload this resume."

*(upload it, wait for it to process)*

> "Behind the scenes, the backend just parsed this resume, matched it
> against a skills taxonomy, and estimated an experience level -- all of
> that feeds into what gets asked next."

**[First generated question, ~40s]** *(show the question, badges)*

> "Here's the first question. Notice it has a topic and a difficulty badge
> -- both driven by what's actually in the resume. Now let me show where
> this question actually came from."

*(click "Why this question?")*

> "This panel shows the exact retrieval query the system built, and the
> exact knowledge-base excerpts it retrieved to ground this question --
> with similarity scores. The question wasn't invented by the model out of
> nothing; it's required to be answerable from this specific retrieved
> context. Every question in this system is traceable back to its source
> like this, all the way down to the database."

**[Answering through the interview, ~60-90s]** *(answer, show feedback, repeat)*

> "I'll answer this."

*(type a real answer, submit, let the score/feedback flash show)*

> "It's scored against that same retrieved context, with specific
> feedback, not just a number. Now watch the next question -- since that
> answer was solid, it moves on to a new topic instead of repeating itself.
> If I'd answered weakly, it would re-probe the same topic at a more basic
> level instead -- that adaptive behavior is driven by the previous
> answer's score."

*(answer through the remaining questions, faster / can speed up in editing)*

**[Final report, ~30s]** *(show the summary page)*

> "And here's the final report: an overall score, a narrative summary,
> strengths and improvement areas, and a score breakdown by topic. Scrolling
> down, the full transcript -- every question, answer, and score -- is
> persisted, not just this summary."

**[Close, ~15s]**

> "Architecture-wise: React frontend, FastAPI backend, a Chroma vector
> store per role built with semantic chunking over the knowledge base, and
> [Groq's LLM for question generation and scoring / deterministic fallback
> logic, since I'm demoing without an API key configured] -- both are
> fully documented in the repo's README. Thanks for watching."

---

## Notes for whoever records this

- If recording without a `GROQ_API_KEY` configured, the system still runs
  end-to-end on deterministic fallback logic (see README's "Without a Groq
  API key" section) -- it's fine to demo either mode, just say out loud
  which one is active, since fallback questions/scoring are visibly simpler.
- Make sure `python scripts/ingest_kb.py` has been run before recording --
  otherwise starting a session will now fail with a 503
  ("knowledge base ... has not been ingested yet") instead of working.
