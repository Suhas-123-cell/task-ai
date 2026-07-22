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

## Notes for whoever records this

- If recording without a `GROQ_API_KEY` configured, the system still runs
  end-to-end on deterministic fallback logic (see README's "Without a Groq
  API key" section) -- it's fine to demo either mode, just say out loud
  which one is active, since fallback questions/scoring are visibly simpler.
- Make sure `python scripts/ingest_kb.py` has been run before recording --
  otherwise starting a session will now fail with a 503
  ("knowledge base ... has not been ingested yet") instead of working.
