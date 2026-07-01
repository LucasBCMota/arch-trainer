import { useEffect, useState } from "react";
import { api } from "../api.js";

// Smart review: the patterns you keep missing, weakest & most-overdue first,
// with one-click "practice" (targeted exercise) or "study" (targeted note).
export default function Review({ onScenario, isOwner = true }) {
  const [items, setItems] = useState([]);
  const [busy, setBusy] = useState(null);
  const [msg, setMsg] = useState(null);
  const [error, setError] = useState(null);

  function load() {
    api.reviewQueue().then(setItems).catch((e) => setError(e.message));
  }
  useEffect(load, []);

  async function practice(pattern) {
    setBusy(pattern);
    setError(null);
    setMsg(null);
    try {
      const pending = await api.createScenario({
        difficulty: "platform",
        focus_area: "any",
        exercise_type: "free_form",
        focus_pattern: pattern,
      });
      const ready = await api.poll(() => api.getScenario(pending.id), {
        where: "“Unanswered scenarios”",
      });
      await api.markReviewed(pattern).catch(() => {});
      onScenario(ready);
    } catch (e) {
      setError(e.message);
      setBusy(null);
    }
  }

  async function study(pattern) {
    setBusy(pattern);
    setError(null);
    setMsg(null);
    try {
      const pending = await api.study(pattern);
      await api.poll(() => api.studyNote(pending.id), { where: "the Study library" });
      await api.markReviewed(pattern).catch(() => {});
      setMsg(`Study note on “${pattern}” added to your library.`);
      load();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <div className="panel">
        <h2>Smart review</h2>
        <p className="muted" style={{ marginTop: -6 }}>
          The patterns you keep missing — weakest and most overdue first. Practice or study each to
          close the gap; it drops down the list once reviewed.
        </p>
        {!isOwner && (
          <p className="muted" style={{ fontSize: 13 }}>Practice/study is owner-only (spends the host's keys).</p>
        )}
        {error && <p className="error">{error}</p>}
        {msg && <p className="muted">{msg}</p>}
      </div>

      {items.length === 0 ? (
        <div className="panel">
          <p className="muted">
            No gaps yet — answer some exercises and the patterns you miss will show up here.
          </p>
        </div>
      ) : (
        <div className="panel">
          <table>
            <thead>
              <tr>
                <th>Pattern</th>
                <th style={{ textAlign: "right" }}>Missed</th>
                <th>Last reviewed</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.pattern_name}>
                  <td>{it.pattern_name}</td>
                  <td className="count">{it.miss_count}</td>
                  <td className="muted mono">
                    {it.last_reviewed_at ? new Date(it.last_reviewed_at).toLocaleDateString() : "never"}
                  </td>
                  <td>
                    {isOwner && (
                      <div className="row" style={{ justifyContent: "flex-end" }}>
                        <button
                          className="ghost"
                          disabled={busy === it.pattern_name}
                          onClick={() => practice(it.pattern_name)}
                        >
                          {busy === it.pattern_name ? "…" : "Practice"}
                        </button>
                        <button
                          className="ghost"
                          disabled={busy === it.pattern_name}
                          onClick={() => study(it.pattern_name)}
                        >
                          Study
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
