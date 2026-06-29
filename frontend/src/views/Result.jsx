import { lazy, Suspense } from "react";
import { api } from "../api.js";
import Markdown from "../Markdown.jsx";
import Mermaid from "../Mermaid.jsx";

const ExcalidrawCanvas = lazy(() => import("../ExcalidrawCanvas.jsx"));

function badgeClass(score) {
  if (score >= 4) return "green";
  if (score === 3) return "yellow";
  return "red";
}

function covClass(status) {
  if (status === "covered") return "green";
  if (status === "partial") return "yellow";
  return "red";
}

function List({ items }) {
  return (
    <ul>
      {items.map((x, i) => (
        <li key={i}>{x}</li>
      ))}
    </ul>
  );
}

export default function Result({ scenario, result, onNext }) {
  const j = result.judgment;
  const ref = result.reference_solution;
  const factual = scenario.exercise_type === "language" || scenario.exercise_type === "algorithms";

  return (
    <>
      <div className="panel">
        <div className="row" style={{ alignItems: "center", gap: 18 }}>
          <span className={`badge ${badgeClass(result.score)}`}>{result.score}</span>
          <div>
            <div className="muted" style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: "0.06em" }}>
              {j.overall_assessment} · {scenario.title}
            </div>
            <div style={{ fontSize: 17, marginTop: 4 }}>{j.one_line_verdict}</div>
          </div>
        </div>
      </div>

      {factual && ref?.summary && (
        <div className="panel">
          <div className="section matched">
            <h3>Reference answer</h3>
            <Markdown>{ref.summary}</Markdown>
            {ref.key_points?.length > 0 && (
              <>
                <label className="field" style={{ marginTop: 10 }}>Key points</label>
                <ul>{ref.key_points.map((p, i) => <li key={i}>{p}</li>)}</ul>
              </>
            )}
            {ref.common_mistakes?.length > 0 && (
              <>
                <label className="field" style={{ marginTop: 10 }}>Common mistakes</label>
                <ul>{ref.common_mistakes.map((p, i) => <li key={i}>{p}</li>)}</ul>
              </>
            )}
          </div>
        </div>
      )}

      {j.requirement_coverage?.length > 0 && (
        <div className="panel">
          <h2>Requirement coverage</h2>
          <table>
            <thead>
              <tr>
                <th>Requirement</th>
                <th>Status</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {j.requirement_coverage.map((r, i) => (
                <tr key={i}>
                  <td>{r.requirement}</td>
                  <td>
                    <span className={`pill ${covClass(r.status)}`}>{r.status}</span>
                  </td>
                  <td className="muted">{r.comment}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {(ref?.diagram_mermaid || result.answer_freehand) && (
        <div className="panel">
          <h2>Diagram</h2>
          <div className="answer-split">
            {ref?.diagram_mermaid && (
              <div>
                <label className="field">Reference architecture</label>
                <Mermaid chart={ref.diagram_mermaid} />
              </div>
            )}
            {result.answer_freehand && (
              <div>
                <label className="field">Your sketch (not graded)</label>
                <Suspense fallback={<p className="muted">Loading…</p>}>
                  <ExcalidrawCanvas initialData={result.answer_freehand} viewMode height={320} />
                </Suspense>
              </div>
            )}
          </div>
        </div>
      )}

      {j.unnamed_patterns?.length > 0 && (
        <div className="panel">
          <div className="section unnamed">
            <h3>You did this but didn't name it</h3>
            {j.unnamed_patterns.map((p, i) => (
              <div className="pat" key={i}>
                <span className="name">{p.pattern_name}</span>
                <div className="muted" style={{ marginTop: 4 }}>{p.what_they_described}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="panel">
        {j.matched_points?.length > 0 && (
          <div className="section matched">
            <h3>Matched the reference</h3>
            <List items={j.matched_points} />
          </div>
        )}
        {j.missed_points?.length > 0 && (
          <div className="section missed">
            <h3>Missed entirely</h3>
            <List items={j.missed_points} />
          </div>
        )}
        {j.communication_gaps?.length > 0 && (
          <div className="section">
            <h3>Communication gaps</h3>
            <List items={j.communication_gaps} />
          </div>
        )}
        {j.genuine_disagreements?.length > 0 && (
          <div className="section">
            <h3>Defensible alternatives</h3>
            <List items={j.genuine_disagreements} />
          </div>
        )}
      </div>

      <div className="panel">
        <details>
          <summary>Full reference solution</summary>
          <pre className="ref">{JSON.stringify(ref, null, 2)}</pre>
        </details>
      </div>

      <div className="row">
        <button className="primary" onClick={onNext}>
          Next scenario
        </button>
        <a className="ghost" href={api.exportUrl}>
          Export all sessions
        </a>
      </div>
    </>
  );
}
