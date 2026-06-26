import { useState } from "react";
import { api } from "../api.js";

export default function Answering({ scenario, onResult, onCancel }) {
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function submit() {
    setLoading(true);
    setError(null);
    try {
      const pending = await api.createSession({
        scenario_id: scenario.id,
        user_answer: answer,
      });
      const ready = await api.poll(() => api.getSession(pending.id));
      onResult(ready);
    } catch (e) {
      setError(e.message);
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="panel" style={{ textAlign: "center", padding: "48px 22px" }}>
        <div className="spinner" />
        <h2 style={{ marginTop: 16 }}>Judging your answer…</h2>
        <p className="muted">
          Queued to the model. This can take a few minutes on slow/free models — keep this tab open;
          your result will appear automatically.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="panel">
        <h2>
          {scenario.difficulty}-level · {scenario.focus_area}
        </h2>
        <h3 style={{ marginTop: 0, fontSize: 20 }}>{scenario.title}</h3>
        <p className="muted">{scenario.context}</p>
        <p>
          <strong>Problem.</strong> {scenario.problem}
        </p>
        {scenario.constraints?.length > 0 && (
          <>
            <label className="field" style={{ marginTop: 14 }}>
              Constraints
            </label>
            <ul className="constraints">
              {scenario.constraints.map((c, i) => (
                <li key={i}>{c}</li>
              ))}
            </ul>
          </>
        )}
      </div>

      <div className="panel">
        <h2>Your answer</h2>
        <textarea
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder="Walk through your design: key decisions, tradeoffs, failure modes, open questions…"
          autoFocus
        />
        <div className="row" style={{ marginTop: 16 }}>
          <button className="primary" onClick={submit} disabled={loading || !answer.trim()}>
            {loading ? "Judging…" : "Submit for judgment"}
          </button>
          <button className="ghost" onClick={onCancel}>
            Cancel
          </button>
        </div>
        {error && <p className="error" style={{ marginTop: 12 }}>{error}</p>}
      </div>
    </>
  );
}
