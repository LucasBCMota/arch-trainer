async function req(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail;
    try {
      detail = (await res.json()).detail;
    } catch {
      detail = await res.text();
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
