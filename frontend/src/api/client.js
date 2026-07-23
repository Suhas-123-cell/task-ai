// Thin fetch wrapper for the FastAPI backend. Kept dependency-free (no axios)
// since the app only needs a handful of calls; every function here mirrors
// exactly one backend endpoint and throws a normal Error with the backend's
// `detail` message on failure so components can show it directly.

// Nullish coalescing (??), not ||: when this app is deployed as a single
// combined service (FastAPI serving these built static files itself, see
// backend/app/main.py), VITE_API_BASE_URL is deliberately set to an empty
// string at build time so requests go to relative /api/... paths on the
// same origin. `||` would treat that empty string as falsy and silently
// fall back to the localhost default, breaking same-origin deployment;
// `??` only falls back when the var is genuinely unset (local dev).
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function handleResponse(response) {
  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // response body wasn't JSON; keep the generic message
    }
    throw new Error(detail);
  }
  return response.json();
}

export async function fetchRoles() {
  const response = await fetch(`${API_BASE_URL}/api/roles`);
  return handleResponse(response);
}

export async function uploadCandidate({ fullName, targetRole, resumeFile }) {
  const formData = new FormData();
  formData.append("full_name", fullName || "Candidate");
  formData.append("target_role", targetRole);
  formData.append("resume", resumeFile);

  const response = await fetch(`${API_BASE_URL}/api/candidates`, {
    method: "POST",
    body: formData,
  });
  return handleResponse(response);
}

export async function startInterviewSession(candidateId) {
  const response = await fetch(`${API_BASE_URL}/api/interview/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ candidate_id: candidateId }),
  });
  return handleResponse(response);
}

export async function submitAnswer(sessionId, answerText) {
  const response = await fetch(`${API_BASE_URL}/api/interview/sessions/${sessionId}/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answer_text: answerText }),
  });
  return handleResponse(response);
}

export async function fetchReport(sessionId) {
  const response = await fetch(`${API_BASE_URL}/api/reports/${sessionId}`);
  return handleResponse(response);
}
