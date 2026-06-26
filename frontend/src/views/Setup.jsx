import { useEffect, useState } from "react";
import { api } from "../api.js";
import ModelInput, { useModelSelection } from "../ModelInput.jsx";

const DIFFICULTIES = ["feature", "platform", "principal"];
const FOCUS_AREAS = [
  "any",
  "concurrency",
  "external boundaries",
  "data modeling",
  "failure modes",
  "scaling",
  "consistency",
];

export default function Setup({ onScenario, isOwner = true }) {
  const [difficulty, setDifficulty] = useState("feature");
  const [focus, setFocus] = useState("any");
  const [models, setModels] = useState(null);
  const [model, setModel] = useModelSelection();
  const [gaps, setGaps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.models().then(setModels).catch((e) => setError(e.message));
    api.patternGaps().then((g) => setGaps(g.slice(0, 5))).catch(() => {});
  }, []);

  async function generate() {
    setLoading(true);
    setError(null);
    try {
      const body = { difficulty, focus_area: focus };
      if (model) body.model = model;
      const pending = await api.createScenario(body); // returns immediately
      const ready = await api.poll(() => api.getScenario(pending.id));
      onScenario(ready);
    } catch (e) {
      setError(e.message);
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="panel" style={{ textAlign: "center", padding: "48px 22px" }}>
        <div className="spinner" />
        <h2 style={{ marginTop: 16 }}>Generating scenario…</h2>
        <p className="muted">
          Queued to the model. Free/slow models can take a few minutes — keep this tab open; it'll
          appear automatically when ready.
        </p>
        {error && <p className="error">{error}</p>}
      </div>
    );
  }

  return (
    <>
      <div className="panel">
        <h2>New exercise</h2>

        <label className="field">Difficulty</label>
        <div className="chips">
          {DIFFICULTIES.map((d) => (
            <button
              key={d}
              className={`chip ${difficulty === d ? "on" : ""}`}
              onClick={() => setDifficulty(d)}
            >
              {d}
            </button>
          ))}
        </div>

        <label className="field">Focus area</label>
        <div className="chips">
          {FOCUS_AREAS.map((f) => (
            <button
              key={f}
              className={`chip ${focus === f ? "on" : ""}`}
              onClick={() => setFocus(f)}
            >
              {f}
            </button>
          ))}
        </div>

        <label className="field">Model</label>
        <ModelInput value={model} onChange={setModel} />
        {models && models.available.length === 0 && (
          <p className="error" style={{ marginTop: 8 }}>
            No provider key configured on the server. Set ANTHROPIC_API_KEY (or OPENAI/OPENROUTER).
          </p>
        )}

        <div style={{ marginTop: 20 }}>
          <button
            className="primary"
            onClick={generate}
            disabled={!isOwner || loading || (models && models.available.length === 0)}
            title={isOwner ? "" : "Owner only — generation spends the host's LLM keys"}
          >
            {loading ? "Generating…" : "Generate scenario"}
          </button>
          {!isOwner && (
            <span className="muted" style={{ marginLeft: 10, fontSize: 13 }}>
              owner only
            </span>
          )}
        </div>
        {error && <p className="error" style={{ marginTop: 12 }}>{error}</p>}
      </div>

      {gaps.length > 0 && (
        <div className="panel">
          <h2>Your recurring gaps</h2>
          <table>
            <tbody>
              {gaps.map((g) => (
                <tr key={g.pattern_name}>
                  <td>{g.pattern_name}</td>
                  <td className="count">{g.count}×</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
