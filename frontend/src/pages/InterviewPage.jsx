import { useState } from "react";
import { submitAnswer } from "../api/client.js";

export default function InterviewPage({ candidate, session, question, onAnswerSubmitted }) {
  const [answerText, setAnswerText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [showContext, setShowContext] = useState(false);
  const [lastFeedback, setLastFeedback] = useState(null);

  const questionNumber = question.index_in_session + 1;
  const totalQuestions = session.max_questions;

  async function handleSubmit(event) {
    event.preventDefault();
    if (!answerText.trim()) {
      setError("Please enter an answer before submitting.");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      const result = await submitAnswer(session.id, answerText);
      setLastFeedback(result.evaluated_answer);
      setAnswerText("");
      setShowContext(false);
      // Reset here, not just in the catch branch: InterviewPage is not remounted
      // between questions (App.jsx just passes a new `question` prop), so without
      // this the disabled state from this submit would silently persist and leave
      // every subsequent question's textarea/button permanently disabled. Found via
      // an end-to-end browser test that answered more than one question in a row.
      setIsSubmitting(false);

      // Small delay so the candidate can see their score/feedback before the
      // next question replaces it -- otherwise scoring feedback would flash
      // and disappear instantly, which user testing found jarring.
      setTimeout(() => {
        setLastFeedback(null);
        onAnswerSubmitted({
          session: result.session,
          nextQuestion: result.next_question,
          isComplete: result.is_complete,
        });
      }, 1800);
    } catch (err) {
      setError(err.message);
      setIsSubmitting(false);
    }
  }

  return (
    <div className="card">
      <p className="muted small interviewing-as">Interviewing: {candidate.full_name}</p>

      <div className="progress-row">
        <span>
          Question {questionNumber} of {totalQuestions}
        </span>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${(questionNumber / totalQuestions) * 100}%` }}
          />
        </div>
      </div>

      <div className="badge-row">
        <span className="badge badge-topic">{question.topic}</span>
        <span className="badge badge-difficulty">{question.difficulty}</span>
      </div>

      <p className="question-text" id="current-question">
        {question.question_text}
      </p>

      <button
        type="button"
        className="link-button"
        aria-expanded={showContext}
        aria-controls="context-panel"
        onClick={() => setShowContext((v) => !v)}
      >
        {showContext ? "Hide" : "Why this question?"}
      </button>

      {showContext && (
        <div className="context-panel" id="context-panel">
          <p className="muted small">
            Retrieved from the knowledge base using query: <em>{question.retrieval_query}</em>
          </p>
          {question.retrieved_context.map((chunk, i) => (
            <div key={`${chunk.source_file}-${chunk.chunk_index ?? i}`} className="context-chunk">
              <div className="context-chunk-header">
                <span>{chunk.source_file}</span>
                <span>relevance {Math.round(chunk.similarity_score * 100)}%</span>
              </div>
              <p>{chunk.text}</p>
            </div>
          ))}
        </div>
      )}

      {lastFeedback ? (
        <div className="feedback-flash" role="status" aria-live="polite">
          <strong>Score: {lastFeedback.score}/5</strong>
          <p>{lastFeedback.feedback}</p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="answer-form">
          <label className="visually-hidden" htmlFor="answer-textarea">
            Your answer
          </label>
          <textarea
            id="answer-textarea"
            aria-labelledby="current-question"
            value={answerText}
            onChange={(e) => setAnswerText(e.target.value)}
            placeholder="Type your answer here..."
            rows={6}
            disabled={isSubmitting}
          />
          {error && (
            <p className="error-text" role="alert" aria-live="assertive">
              {error}
            </p>
          )}
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Submitting..." : "Submit Answer"}
          </button>
        </form>
      )}
    </div>
  );
}
