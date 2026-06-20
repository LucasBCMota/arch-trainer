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
};
