import { useEffect, useState } from "react";
import { api } from "../api.js";

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

export default function Setup({ onScenario }) {
  const [difficulty, setDifficulty] = useState("feature");
  const [focus, setFocus] = useState("any");
  const [models, setModels] = useState(null);
  const [model, setModel] = useState("");
  const [gaps, setGaps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.models().then(setModels).catch((e) => setError(e.message));
    api.patternGaps().then((g) => setGaps(g.slice(0, 5))).catch(() => {});
  }, []);

  // flatten suggested provider->models into "provider:model" options
  const modelOptions = models
    ? Object.entries(models.suggested).flatMap(([prov, ids]) =>
        ids.map((id) => `${prov}:${id}`)
      )
    : [];

  async function generate() {
    setLoading(true);
    setError(null);
    try {
      const body = { difficulty, focus_area: focus };
      if (model) body.model = model;
      const sc = await api.createScenario(body);
      onScenario(sc);
    } catch (e) {
      setError(e.message);
      setLoading(false);
    }
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
        {models && models.available.length === 0 ? (
          <p className="error">
            No provider key configured. Set ANTHROPIC_API_KEY (or OPENAI/OPENROUTER) in the backend
            env.
          </p>
        ) : (
          <select value={model} onChange={(e) => setModel(e.target.value)}>
            <option value="">default ({models ? models.current : "…"})</option>
            {modelOptions.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        )}

        <div style={{ marginTop: 20 }}>
          <button
            className="primary"
            onClick={generate}
            disabled={loading || (models && models.available.length === 0)}
          >
            {loading ? "Generating…" : "Generate scenario"}
          </button>
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
