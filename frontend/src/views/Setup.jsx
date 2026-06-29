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

const EXERCISE_TYPES = [
  ["free_form", "free-form"],
  ["structured", "structured design"],
  ["language", "language gotcha"],
  ["algorithms", "algorithms"],
];

const LANGUAGES = ["Python", "JavaScript", "TypeScript", "Java", "C++", "Go", "Rust", "SQL", "C#", "Ruby"];

export default function Setup({ onScenario, isOwner = true }) {
  const [difficulty, setDifficulty] = useState("feature");
  const [focus, setFocus] = useState("any");
  const [exerciseType, setExerciseType] = useState("free_form");
  const [language, setLanguage] = useState("Python");
  const [models, setModels] = useState(null);
  const [model, setModel] = useModelSelection();
  const [gaps, setGaps] = useState([]);
  const [mine, setMine] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.models().then(setModels).catch((e) => setError(e.message));
    api.patternGaps().then((g) => setGaps(g.slice(0, 5))).catch(() => {});
    api.listScenarios().then(setMine).catch(() => {});
  }, []);

  const unanswered = mine.filter((s) => !s.answered);
  const answered = mine.filter((s) => s.answered);

  async function generate() {
    setLoading(true);
    setError(null);
    try {
      const body = { difficulty, focus_area: focus, exercise_type: exerciseType };
      if (exerciseType === "language" || exerciseType === "algorithms") body.language = language;
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

        <label className="field">Exercise type</label>
        <div className="chips">
          {EXERCISE_TYPES.map(([val, label]) => (
            <button
              key={val}
              className={`chip ${exerciseType === val ? "on" : ""}`}
              onClick={() => {
                setExerciseType(val);
                // 'any' is only valid for algorithms — coerce when switching to gotchas.
                if (val === "language" && language === "any") setLanguage("Python");
              }}
              title={
                val === "structured"
                  ? "Templated answer + architecture diagram; graded on per-requirement coverage"
                  : "Free-text answer; graded on reasoning + naming patterns"
              }
            >
              {label}
            </button>
          ))}
        </div>

        {(exerciseType === "language" || exerciseType === "algorithms") && (
          <>
            <label className="field">Language</label>
            <select value={language} onChange={(e) => setLanguage(e.target.value)} style={{ maxWidth: 220 }}>
              {exerciseType === "algorithms" && <option value="any">any</option>}
              {LANGUAGES.map((l) => (
                <option key={l} value={l}>
                  {l}
                </option>
              ))}
            </select>
          </>
        )}

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

      {unanswered.length > 0 && (
        <div className="panel">
          <h2>Unanswered scenarios</h2>
          <p className="muted" style={{ marginTop: -6 }}>
            Generated but not yet answered (e.g. you closed the tab). Pick up where you left off.
          </p>
          <ul className="note-list">
            {unanswered.map((s) => (
              <li key={s.id}>
                <button className="link" onClick={() => onScenario(s)}>
                  {s.title || "(untitled)"}
                </button>
                <span className="muted mono"> · {s.difficulty} · {s.focus_area}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {answered.length > 0 && (
        <div className="panel">
          <h2>Re-attempt a scenario</h2>
          <p className="muted" style={{ marginTop: -6 }}>
            Answer an old scenario again — it records a fresh attempt, leaving your earlier one intact.
          </p>
          <ul className="note-list">
            {answered.map((s) => (
              <li key={s.id}>
                <span>
                  {s.title || "(untitled)"}
                  <span className="muted mono"> · {s.difficulty}</span>
                </span>
                <button className="ghost" onClick={() => onScenario(s)}>
                  Answer again
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

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
