import { useEffect, useState } from "react";
import { api } from "../api.js";
import Markdown from "../Markdown.jsx";

export default function Public() {
  const [notes, setNotes] = useState([]);
  const [refs, setRefs] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.publicNotes().then(setNotes).catch((e) => setError(e.message));
    api.publicReferences().then(setRefs).catch(() => {});
  }, []);

  return (
    <>
      <div className="panel">
        <h2>Public library</h2>
        <p className="muted" style={{ marginTop: -6 }}>
          Study notes, cheat-sheets, and reference designs other users have made public.
        </p>
        {error && <p className="error">{error}</p>}
      </div>

      {notes.length === 0 && refs.length === 0 && (
        <div className="panel">
          <p className="muted">Nothing public yet.</p>
        </div>
      )}

      {notes.map((n) => (
        <div className="panel" key={n.id}>
          <h3 style={{ margin: 0 }}>{n.topic}</h3>
          <p className="muted mono" style={{ marginTop: 2 }}>
            {n.kind} · by {n.author || "someone"}
          </p>
          <Markdown>{n.content_md}</Markdown>
        </div>
      ))}

      {refs.map((r) => (
        <div className="panel" key={r.id}>
          <h3 style={{ margin: 0 }}>{r.title}</h3>
          <p className="muted mono" style={{ marginTop: 2 }}>
            reference design · {r.difficulty} · by {r.author || "someone"}
          </p>
          <p>{r.reference_solution.summary}</p>
          <details>
            <summary>Full reference solution</summary>
            <pre className="ref">{JSON.stringify(r.reference_solution, null, 2)}</pre>
          </details>
        </div>
      ))}
    </>
  );
}
