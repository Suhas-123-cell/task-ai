import { useEffect, useState } from "react";
import { fetchRoles, startInterviewSession, uploadCandidate } from "../api/client.js";

export default function UploadPage({ onInterviewStarted }) {
  const [roles, setRoles] = useState([]);
  const [fullName, setFullName] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [resumeFile, setResumeFile] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchRoles()
      .then((fetchedRoles) => {
        setRoles(fetchedRoles);
        if (fetchedRoles.length > 0) setTargetRole(fetchedRoles[0].slug);
      })
      .catch((err) => setError(err.message));
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!resumeFile || !targetRole) {
      setError("Please select a role and choose a resume file.");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      const candidate = await uploadCandidate({ fullName, targetRole, resumeFile });
      const { session, question } = await startInterviewSession(candidate.id);
      onInterviewStarted({ candidate, session, question });
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="card">
      <h2>Start a Screening Interview</h2>
      <p className="muted">
        Upload a resume (PDF or .txt) and pick a target role. Questions will be generated from a
        role-specific knowledge base, grounded in your actual resume content.
      </p>

      <form onSubmit={handleSubmit} className="upload-form">
        <label>
          Candidate name
          <input
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Jane Doe"
          />
        </label>

        <label>
          Target role
          <select value={targetRole} onChange={(e) => setTargetRole(e.target.value)} required>
            {roles.map((role) => (
              <option key={role.slug} value={role.slug}>
                {role.display_name}
              </option>
            ))}
          </select>
          {roles.find((r) => r.slug === targetRole) && (
            <span className="field-hint">{roles.find((r) => r.slug === targetRole).description}</span>
          )}
        </label>

        <label>
          Resume (PDF or .txt)
          <input
            type="file"
            accept=".pdf,.txt"
            onChange={(e) => setResumeFile(e.target.files[0] ?? null)}
            required
          />
        </label>

        {error && <p className="error-text">{error}</p>}

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Starting interview..." : "Start Interview"}
        </button>
      </form>
    </div>
  );
}
