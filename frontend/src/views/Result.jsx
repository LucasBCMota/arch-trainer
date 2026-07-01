import { lazy, Suspense, useState } from "react";
import { api } from "../api.js";
import Markdown from "../Markdown.jsx";
import Mermaid from "../Mermaid.jsx";
import Tabs from "../Tabs.jsx";

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

  const hasVerdict =
    j.matched_points?.length ||
    j.missed_points?.length ||
    j.communication_gaps?.length ||
    j.genuine_disagreements?.length;
  const hasCoverage = j.requirement_coverage?.length > 0;
  const hasDiagram = !!ref?.diagram_mermaid || !!result.answer_freehand;
  const hasPatterns = j.unnamed_patterns?.length > 0;

  const tabs = [
    { key: "verdict", label: "Verdict", hidden: !hasVerdict },
    { key: "coverage", label: "Requirement coverage", hidden: !hasCoverage },
    { key: "diagram", label: "Diagram", hidden: !hasDiagram },
    { key: "patterns", label: "Unnamed patterns", hidden: !hasPatterns },
    { key: "reference", label: "Reference", hidden: false },
  ];
  const firstVisible = tabs.find((t) => !t.hidden).key;
  const [tab, setTab] = useState(factual ? "reference" : firstVisible);

  return (
    <>
      <div className="panel">
        <div className="row" style={{ alignItems: "center", gap: 18 }}>
          <span className={`badge ${badgeClass(result.score)}`}>{result.score}</span>
          <div>
            <div className="muted" style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: "0.06em" }}>
              {j.overall_assessment} · {scenario.title}
            </div>
            <div style={{ fontSize: 18, marginTop: 4 }}>{j.one_line_verdict}</div>
          </div>
        </div>
      </div>

      <Tabs tabs={tabs} active={tab} onChange={setTab} />

      <div className="panel">
        {tab === "verdict" && (
          <>
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
          </>
        )}

        {tab === "coverage" && (
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
        )}

        {tab === "diagram" && (
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
        )}

        {tab === "patterns" && (
          <div className="section unnamed">
            <h3>You did this but didn't name it</h3>
            {j.unnamed_patterns.map((p, i) => (
              <div className="pat" key={i}>
                <span className="name">{p.pattern_name}</span>
                <div className="muted" style={{ marginTop: 4 }}>{p.what_they_described}</div>
              </div>
            ))}
          </div>
        )}

        {tab === "reference" && (
          <>
            {factual && ref?.summary && (
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
            )}
            <details style={{ marginTop: factual ? 14 : 0 }}>
              <summary>Full reference solution</summary>
              <pre className="ref">{JSON.stringify(ref, null, 2)}</pre>
            </details>
          </>
        )}
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
