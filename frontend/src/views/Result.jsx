import { api } from "../api.js";

function badgeClass(score) {
  if (score >= 4) return "green";
  if (score === 3) return "yellow";
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
