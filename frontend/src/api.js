async function req(path, options = {}) {
  // Abort long-hung requests (e.g. a slow model behind a proxy) with a clear
  // message instead of a bare "Failed to fetch".
  const controller = new AbortController();
  const timeoutMs = options.timeoutMs ?? 180000;
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  let res;
  try {
    res = await fetch(`/api${path}`, {
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      ...options,
    });
  } catch (e) {
    if (e.name === "AbortError") {
      throw new Error(
        `Request timed out after ${Math.round(timeoutMs / 1000)}s — the model may be too slow. ` +
          "Try a faster model."
      );
    }
    throw new Error(
      "Failed to reach the server (network error, or the request was dropped mid-flight)."
    );
  } finally {
    clearTimeout(timer);
  }
  if (!res.ok) {
    // Read the body exactly once (a fetch body can't be read twice), then try
    // to pull `detail` out of JSON, falling back to the raw text.
    const body = await res.text();
    let detail = body;
    try {
      detail = JSON.parse(body).detail ?? body;
    } catch {
      // body wasn't JSON — keep the raw text
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json();
}

export const api = {
  me: () => req("/me"),
  // Auth0 BFF: these are full-page redirects, not fetches.
  loginUrl: "/api/auth/login",
  googleLoginUrl: "/api/auth/login?connection=google-oauth2",
  logoutUrl: "/api/auth/logout",
  models: () => req("/models"),
  createScenario: (body) =>
    req("/scenarios", { method: "POST", body: JSON.stringify(body) }),
  createSession: (body) =>
    req("/sessions", { method: "POST", body: JSON.stringify(body) }),
  listSessions: () => req("/sessions"),
  patternGaps: () => req("/stats/pattern-gaps"),
  summary: () => req("/stats/summary"),
  exportUrl: "/api/sessions/export",

  // study + artifacts
  study: (topic, model) =>
    req("/study", { method: "POST", body: JSON.stringify({ topic, model: model || null }) }),
  cheatsheet: (topic, model) =>
    req("/cheatsheets", { method: "POST", body: JSON.stringify({ topic, model: model || null }) }),
  importNote: (body) =>
    req("/study-notes", { method: "POST", body: JSON.stringify(body) }),
  studyNotes: (params = "") => req(`/study-notes${params}`),
  updateNote: (id, body) =>
    req(`/study-notes/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  pinNote: (id, pinned) =>
    req(`/study-notes/${id}/pin`, { method: "POST", body: JSON.stringify({ pinned }) }),
  deleteNote: (id) => req(`/study-notes/${id}`, { method: "DELETE" }),
  references: () => req("/artifacts/references"),
  pinScenario: (id, pinned) =>
    req(`/scenarios/${id}/pin`, { method: "POST", body: JSON.stringify({ pinned }) }),

  // visibility toggles (private⇄public)
  setNoteVisibility: (id, visibility) =>
    req(`/study-notes/${id}/visibility`, { method: "POST", body: JSON.stringify({ visibility }) }),
  setScenarioVisibility: (id, visibility) =>
    req(`/scenarios/${id}/visibility`, { method: "POST", body: JSON.stringify({ visibility }) }),
  setSessionVisibility: (id, visibility) =>
    req(`/sessions/${id}/visibility`, { method: "POST", body: JSON.stringify({ visibility }) }),

  // public browse
  publicNotes: () => req("/public/study-notes"),
  publicReferences: () => req("/public/references"),

  // owner-only: claim pre-auth rows
  claimLegacy: () => req("/admin/claim-legacy", { method: "POST" }),

  // per-user favorite models
  setFavoriteModels: (models) =>
    req("/me/favorite-models", { method: "PUT", body: JSON.stringify({ models }) }),
};
