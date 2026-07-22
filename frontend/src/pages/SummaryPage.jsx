import { useEffect, useState } from "react";
import { fetchReport } from "../api/client.js";

export default function SummaryPage({ sessionId, onRestart }) {
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchReport(sessionId)
      .then(setReport)
      .catch((err) => setError(err.message));
  }, [sessionId]);

  if (error) {
    return (
      <div className="card">
        <p className="error-text">{error}</p>
        <button onClick={onRestart}>Start a new interview</button>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="card">
        <p className="muted">Generating your report...</p>
      </div>
    );
  }

  const maxTopicScore = 5;

  return (
    <div className="card">
      <h2>Interview Summary</h2>

      <div className="overall-score">
        <span className="overall-score-number">{report.overall_score.toFixed(1)}</span>
        <span className="overall-score-label">/ 5 overall</span>
      </div>

      <p>{report.summary_text}</p>

      <div className="insights-grid">
        <div>
          <h3>Strengths</h3>
          <ul>
            {report.strengths.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3>Areas to Improve</h3>
          <ul>
            {report.improvement_areas.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      </div>

      <h3>Topic Breakdown</h3>
      <div className="topic-breakdown">
        {report.topic_breakdown.map((t) => (
          <div key={t.topic} className="topic-bar-row">
            <span className="topic-bar-label">{t.topic}</span>
            <div className="topic-bar-track">
              <div
                className="topic-bar-fill"
                style={{ width: `${(t.average_score / maxTopicScore) * 100}%` }}
              />
            </div>
            <span className="topic-bar-score">{t.average_score.toFixed(1)}</span>
          </div>
        ))}
      </div>

      <h3>Full Transcript</h3>
      <div className="transcript">
        {report.qa_pairs.map((pair, i) => (
          <div key={pair.question.id} className="transcript-item">
            <p className="transcript-question">
              Q{i + 1}. {pair.question.question_text}
            </p>
            <p className="transcript-answer">{pair.answer ? pair.answer.answer_text : "(no answer)"}</p>
            {pair.answer && (
              <p className="transcript-feedback">
                Score: {pair.answer.score}/5 -- {pair.answer.feedback}
              </p>
            )}
          </div>
        ))}
      </div>

      <button onClick={onRestart}>Start a new interview</button>
    </div>
  );
}
