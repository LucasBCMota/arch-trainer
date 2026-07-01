import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";

const TYPES = [
  ["free_form", "free-form"],
  ["structured", "structured"],
  ["language", "language"],
  ["algorithms", "algorithms"],
];
const DIFFS = ["feature", "platform", "principal"];

function langFor(type) {
  if (type === "language") return "Python";
  if (type === "algorithms") return "any";
  return undefined;
}

// Timed mock-interview: config → sequential timed questions (no hints) → summary.
export default function Interview({ isOwner = true, onGoReview }) {
  const [phase, setPhase] = useState("config"); // config | generating | answering | judging | summary
  const [count, setCount] = useState(5);
  const [difficulty, setDifficulty] = useState("platform");
  const [types, setTypes] = useState(["free_form"]);
  const [seconds, setSeconds] = useState(300);

  const [runId, setRunId] = useState(null);
  const [index, setIndex] = useState(0);
  const [scenario, setScenario] = useState(null);
  const [answer, setAnswer] = useState("");
  const [timeLeft, setTimeLeft] = useState(0);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);
  const submitting = useRef(false);

  function toggleType(t) {
    setTypes((ts) => (ts.includes(t) ? ts.filter((x) => x !== t) : [...ts, t]));
  }

  async function start() {
    setError(null);
    try {
      const run = await api.createInterview({
        count,
        difficulty,
        exercise_types: types,
        seconds,
      });
      setRunId(run.id);
      setIndex(0);
      generate(run.id, 0);
    } catch (e) {
      setError(e.message);
    }
  }

  async function generate(rid, i) {
    setPhase("generating");
    setError(null);
    setAnswer("");
    const type = types[i % types.length];
    try {
      const pending = await api.createScenario({
        difficulty,
        focus_area: "any",
        exercise_type: type,
        language: langFor(type),
      });
      const ready = await api.poll(() => api.getScenario(pending.id), { where: "your history" });
      setScenario(ready);
      setTimeLeft(seconds);
      setPhase("answering");
    } catch (e) {
      setError(e.message);
      setPhase("config");
    }
  }

  async function submit() {
    if (submitting.current) return;
    submitting.current = true;
    setPhase("judging");
    try {
      const pending = await api.createSession({
        scenario_id: scenario.id,
        user_answer: answer || "(no answer)",
        run_id: runId,
      });
      await api.poll(() => api.getSession(pending.id), { where: "the Dashboard" });
    } catch (e) {
      // keep going even if one judging fails — the summary just omits it
    }
    submitting.current = false;
    const next = index + 1;
    if (next >= count) finish();
    else {
      setIndex(next);
      generate(runId, next);
    }
  }

  async function finish() {
    setPhase("judging");
    try {
      const s = await api.interviewSummary(runId);
      setSummary(s);
      setPhase("summary");
    } catch (e) {
      setError(e.message);
      setPhase("summary");
    }
  }

  // Countdown while answering; auto-submit at zero.
  useEffect(() => {
    if (phase !== "answering") return;
    if (timeLeft <= 0) {
      submit();
      return;
    }
    const t = setTimeout(() => setTimeLeft((s) => s - 1), 1000);
    return () => clearTimeout(t);
  }, [phase, timeLeft]); // eslint-disable-line react-hooks/exhaustive-deps

  const mmss = `${String(Math.floor(timeLeft / 60)).padStart(2, "0")}:${String(timeLeft % 60).padStart(2, "0")}`;

  if (!isOwner) {
    return (
      <div className="panel">
        <h2>Interview mode</h2>
        <p className="muted">Owner-only — it generates and judges exercises (spends the host's keys).</p>
      </div>
    );
  }

  if (phase === "config") {
    return (
      <div className="panel">
        <h2>Interview mode</h2>
        <p className="muted" style={{ marginTop: -6 }}>
          A timed run of several exercises, back to back, no hints — then a summary.
        </p>
        <label className="field">Questions</label>
        <select value={count} onChange={(e) => setCount(+e.target.value)} style={{ maxWidth: 120 }}>
          {[3, 5, 7, 10].map((n) => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
        <label className="field">Difficulty</label>
        <div className="chips">
          {DIFFS.map((d) => (
            <button key={d} className={`chip ${difficulty === d ? "on" : ""}`} onClick={() => setDifficulty(d)}>
              {d}
            </button>
          ))}
        </div>
        <label className="field">Exercise types</label>
        <div className="chips">
          {TYPES.map(([val, label]) => (
            <button key={val} className={`chip ${types.includes(val) ? "on" : ""}`} onClick={() => toggleType(val)}>
              {label}
            </button>
          ))}
        </div>
        <label className="field">Time per question</label>
        <select value={seconds} onChange={(e) => setSeconds(+e.target.value)} style={{ maxWidth: 160 }}>
          {[120, 180, 300, 600].map((s) => (
            <option key={s} value={s}>{s / 60} min</option>
          ))}
        </select>
        <div style={{ marginTop: 20 }}>
          <button className="primary" onClick={start} disabled={types.length === 0}>
            Start interview
          </button>
        </div>
        {error && <p className="error" style={{ marginTop: 12 }}>{error}</p>}
      </div>
    );
  }

  if (phase === "generating" || phase === "judging") {
    return (
      <div className="panel" style={{ textAlign: "center", padding: "48px 22px" }}>
        <div className="spinner" />
        <h2 style={{ marginTop: 16 }}>
          {phase === "generating" ? `Preparing question ${index + 1}…` : "Judging…"}
        </h2>
        <p className="muted">Keep this tab open.</p>
        {error && <p className="error">{error}</p>}
      </div>
    );
  }

  if (phase === "answering") {
    return (
      <>
        <div className="panel">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div className="muted" style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: "0.06em" }}>
              Question {index + 1} / {count} · {scenario.exercise_type}
              {scenario.language ? ` · ${scenario.language}` : ""}
            </div>
            <span className={`badge ${timeLeft < 30 ? "red" : timeLeft < 60 ? "yellow" : "green"}`} style={{ width: "auto", height: "auto", padding: "4px 12px", fontSize: 18 }}>
              {mmss}
            </span>
          </div>
          <h3 style={{ margin: "6px 0 8px", fontSize: 21 }}>{scenario.title}</h3>
          <p className="muted">{scenario.context}</p>
          <p><strong>Problem.</strong> {scenario.problem}</p>
          {scenario.constraints?.length > 0 && (
            <ul className="constraints">
              {scenario.constraints.map((c, i) => <li key={i}>{c}</li>)}
            </ul>
          )}
        </div>
        <div className="panel">
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Your answer… (auto-submits when the timer hits zero)"
            autoFocus
          />
          <div className="row" style={{ marginTop: 16 }}>
            <button className="primary" onClick={submit}>
              {index + 1 >= count ? "Submit & finish" : "Submit & next"}
            </button>
          </div>
        </div>
      </>
    );
  }

  // summary
  return (
    <>
      <div className="panel">
        <h2>Interview complete</h2>
        <div className="stat-row">
          <div className="stat">
            <div className="num">{summary?.average_score ?? "—"}</div>
            <div className="lbl">avg score</div>
          </div>
          <div className="stat">
            <div className="num">{summary?.answered ?? 0}</div>
            <div className="lbl">answered</div>
          </div>
        </div>
      </div>
      {summary?.per_question?.length > 0 && (
        <div className="panel">
          <h2>Per question</h2>
          <table>
            <tbody>
              {summary.per_question.map((q, i) => (
                <tr key={i}>
                  <td>{q.title}</td>
                  <td className="count">{q.score}</td>
                  <td className="muted">{q.one_line_verdict}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {summary?.missed_patterns?.length > 0 && (
        <div className="panel">
          <h2>Patterns to review</h2>
          <table>
            <tbody>
              {summary.missed_patterns.map((p) => (
                <tr key={p.pattern_name}>
                  <td>{p.pattern_name}</td>
                  <td className="count">{p.count}×</td>
                </tr>
              ))}
            </tbody>
          </table>
          {onGoReview && (
            <button className="ghost" style={{ marginTop: 10 }} onClick={onGoReview}>
              Go to Smart review →
            </button>
          )}
        </div>
      )}
      <div className="row">
        <button className="primary" onClick={() => setPhase("config")}>
          New interview
        </button>
      </div>
    </>
  );
}
