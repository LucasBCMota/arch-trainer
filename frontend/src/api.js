async function req(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
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
  login: (password) =>
    req("/login", { method: "POST", body: JSON.stringify({ password }) }),
  logout: () => req("/logout", { method: "POST" }),
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
};
