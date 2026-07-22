import { useState } from "react";
import UploadPage from "./pages/UploadPage.jsx";
import InterviewPage from "./pages/InterviewPage.jsx";
import SummaryPage from "./pages/SummaryPage.jsx";

// Deliberately no router library: the interview is a strictly linear,
// three-stage wizard (upload -> interview -> summary), and a single stage
// variable in the top-level component is simpler and easier to reason about
// than URL-based routing for a flow that never needs deep-linking or
// back/forward navigation between stages.
const STAGES = {
  UPLOAD: "upload",
  INTERVIEW: "interview",
  SUMMARY: "summary",
};

export default function App() {
  const [stage, setStage] = useState(STAGES.UPLOAD);
  const [candidate, setCandidate] = useState(null);
  const [session, setSession] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);

  function handleInterviewStarted({ candidate: newCandidate, session: newSession, question }) {
    setCandidate(newCandidate);
    setSession(newSession);
    setCurrentQuestion(question);
    setStage(STAGES.INTERVIEW);
  }

  function handleAnswerSubmitted({ session: updatedSession, nextQuestion, isComplete }) {
    setSession(updatedSession);
    if (isComplete) {
      setStage(STAGES.SUMMARY);
    } else {
      setCurrentQuestion(nextQuestion);
    }
  }

  function handleRestart() {
    setCandidate(null);
    setSession(null);
    setCurrentQuestion(null);
    setStage(STAGES.UPLOAD);
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>AI Candidate Screening</h1>
        <p className="app-subtitle">RAG-driven role-specific technical interviews</p>
      </header>

      <main className="app-main">
        {stage === STAGES.UPLOAD && <UploadPage onInterviewStarted={handleInterviewStarted} />}
        {stage === STAGES.INTERVIEW && candidate && session && currentQuestion && (
          <InterviewPage
            candidate={candidate}
            session={session}
            question={currentQuestion}
            onAnswerSubmitted={handleAnswerSubmitted}
          />
        )}
        {stage === STAGES.SUMMARY && session && (
          <SummaryPage sessionId={session.id} onRestart={handleRestart} />
        )}
      </main>
    </div>
  );
}
