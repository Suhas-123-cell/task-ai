// Shared score -> color-class mapping, used anywhere a numeric score (out of
// 5) is displayed. Threshold matches the backend's own weak-answer cutoff
// (query_builder.py's _WEAK_SCORE_THRESHOLD = 3.0), so "red" in the UI means
// exactly what triggers the adaptive re-probe server-side.
export function scoreColorClass(score) {
  if (score < 3) return "score-low";
  if (score < 4) return "score-mid";
  return "score-high";
}
