import { useEffect, useState } from "react";
import { api } from "../api.js";

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [gaps, setGaps] = useState([]);
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    api.summary().then(setSummary).catch(() => {});
    api.patternGaps().then(setGaps).catch(() => {});
    api.listSessions().then(setSessions).catch(() => {});
  }, []);

  return (
    <>
      <div className="panel">
        <h2>Overview</h2>
        <div className="stat-row">
          <div className="stat">
            <div className="num">{summary ? summary.total_sessions : "—"}</div>
            <div className="lbl">sessions</div>
          </div>
          <div className="stat">
            <div className="num">
              {summary && summary.average_score != null ? summary.average_score : "—"}
            </div>
            <div className="lbl">avg score</div>
          </div>
        </div>
        <a className="ghost" href={api.exportUrl}>
          Export all sessions
        </a>
      </div>

      <div className="panel">
        <h2>Recurring unnamed patterns</h2>
        {gaps.length === 0 ? (
          <p className="muted">No pattern gaps recorded yet.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Pattern</th>
                <th style={{ textAlign: "right" }}>Times missed</th>
              </tr>
            </thead>
            <tbody>
              {gaps.map((g) => (
                <tr key={g.pattern_name}>
                  <td>{g.pattern_name}</td>
                  <td className="count">{g.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="panel">
        <h2>Session log</h2>
        {sessions.length === 0 ? (
          <p className="muted">No sessions yet.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>When</th>
                <th>Score</th>
                <th>Verdict</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((s) => (
                <tr key={s.id}>
                  <td className="mono muted">{new Date(s.created_at).toLocaleString()}</td>
                  <td className="count">{s.score}</td>
                  <td>{s.judgment?.one_line_verdict}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
