import { useEffect, useState } from "react";
import { api } from "../api.js";
import Markdown from "../Markdown.jsx";
import ModelInput, { useModelSelection } from "../ModelInput.jsx";
import { ImportForm } from "./Study.jsx";

const TABS = [
  ["references", "Reference designs"],
  ["cheatsheets", "Cheat-sheets"],
  ["pinned", "Pinned"],
];

export default function Artifacts({ isOwner = true }) {
  const [tab, setTab] = useState("references");
  return (
    <>
      <div className="tabs">
        {TABS.map(([key, label]) => (
          <button
            key={key}
            className={`tab ${tab === key ? "on" : ""}`}
            onClick={() => setTab(key)}
          >
            {label}
          </button>
        ))}
      </div>
      {tab === "references" && <References />}
      {tab === "cheatsheets" && <CheatSheets isOwner={isOwner} />}
      {tab === "pinned" && <Pinned />}
    </>
  );
}

function ReferenceCard({ r, onPin, onVis }) {
  const ref = r.reference_solution;
  return (
    <div className="panel">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h3 style={{ margin: 0 }}>{r.title}</h3>
        <div className="row">
          <button className="ghost" onClick={() => onVis(r)}>
            {r.visibility === "public" ? "🌐 public" : "🔒 private"}
          </button>
          <button className="ghost" onClick={() => onPin(r)}>
            {r.pinned ? "★ pinned" : "☆ pin"}
          </button>
        </div>
      </div>
      <p className="muted mono" style={{ marginTop: 2 }}>
        {r.difficulty} · {r.focus_area} · {r.model}
      </p>
      <p>{ref.summary}</p>
      <details>
        <summary>Full reference solution</summary>
        <pre className="ref">{JSON.stringify(ref, null, 2)}</pre>
      </details>
    </div>
  );
}

function References() {
  const [refs, setRefs] = useState([]);
  const [error, setError] = useState(null);
  useEffect(() => {
    api.references().then(setRefs).catch((e) => setError(e.message));
  }, []);

  async function pin(r) {
    const u = await api.pinScenario(r.id, !r.pinned);
    setRefs((xs) => xs.map((x) => (x.id === r.id ? { ...x, pinned: u.pinned } : x)));
  }
  async function vis(r) {
    const next = r.visibility === "public" ? "private" : "public";
    const u = await api.setScenarioVisibility(r.id, next);
    setRefs((xs) => xs.map((x) => (x.id === r.id ? { ...x, visibility: u.visibility } : x)));
  }

  if (error) return <p className="error">{error}</p>;
  if (refs.length === 0)
    return (
      <div className="panel">
        <p className="muted">
          No reference designs yet — answer a scenario and its reference solution shows up here.
        </p>
      </div>
    );
  return refs.map((r) => <ReferenceCard key={r.id} r={r} onPin={pin} onVis={vis} />);
}

function CheatSheets({ isOwner = true }) {
  const [notes, setNotes] = useState([]);
  const [model, setModel] = useModelSelection();
  const [topic, setTopic] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [showImport, setShowImport] = useState(false);

  useEffect(() => {
    api.studyNotes("?kind=cheat_sheet").then(setNotes).catch((e) => setError(e.message));
  }, []);

  async function generate() {
    if (!topic.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const pending = await api.cheatsheet(topic, model); // queued
      const n = await api.poll(() => api.studyNote(pending.id));
      setNotes((xs) => [n, ...xs]);
      setTopic("");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function pin(n) {
    const u = await api.pinNote(n.id, !n.pinned);
    setNotes((xs) => xs.map((x) => (x.id === n.id ? u : x)));
  }
  async function remove(id) {
    await api.deleteNote(id).catch(() => {});
    setNotes((xs) => xs.filter((x) => x.id !== id));
  }
  async function vis(n) {
    const next = n.visibility === "public" ? "private" : "public";
    const u = await api.setNoteVisibility(n.id, next);
    setNotes((xs) => xs.map((x) => (x.id === n.id ? u : x)));
  }

  return (
    <>
      <div className="panel">
        <h2>Make a cheat-sheet</h2>
        {isOwner && <ModelInput value={model} onChange={setModel} />}
        <div className="row" style={{ marginTop: 12 }}>
          {isOwner && (
            <>
              <input
                className="text-input"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Pattern name"
                onKeyDown={(e) => e.key === "Enter" && generate()}
              />
              <button className="primary" disabled={busy || !topic.trim()} onClick={generate}>
                {busy ? "Generating…" : "Generate"}
              </button>
            </>
          )}
          <button className="ghost" onClick={() => setShowImport((s) => !s)}>
            {showImport ? "Close import" : "Paste / import"}
          </button>
        </div>
        {error && <p className="error" style={{ marginTop: 10 }}>{error}</p>}
        {showImport && (
          <ImportForm
            kind="cheat_sheet"
            onSaved={(n) => {
              setNotes((xs) => [n, ...xs]);
              setShowImport(false);
            }}
          />
        )}
      </div>

      {notes.map((n) => (
        <div className="panel" key={n.id}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <h3 style={{ margin: 0 }}>{n.topic}</h3>
            <div className="row">
              <button className="ghost" onClick={() => vis(n)}>
                {n.visibility === "public" ? "🌐" : "🔒"}
              </button>
              <button className="ghost" onClick={() => pin(n)}>
                {n.pinned ? "★" : "☆"}
              </button>
              <button className="ghost" onClick={() => remove(n.id)}>
                delete
              </button>
            </div>
          </div>
          <p className="muted mono" style={{ marginTop: 2 }}>{n.model}</p>
          <Markdown>{n.content_md}</Markdown>
        </div>
      ))}
    </>
  );
}

function Pinned() {
  const [notes, setNotes] = useState([]);
  const [refs, setRefs] = useState([]);
  useEffect(() => {
    api.studyNotes("?pinned=true").then(setNotes).catch(() => {});
    api.references().then((rs) => setRefs(rs.filter((r) => r.pinned))).catch(() => {});
  }, []);

  if (notes.length === 0 && refs.length === 0)
    return (
      <div className="panel">
        <p className="muted">Nothing pinned yet. Star a study note, cheat-sheet, or reference design.</p>
      </div>
    );

  return (
    <>
      {notes.map((n) => (
        <div className="panel" key={n.id}>
          <h3 style={{ margin: 0 }}>★ {n.topic}</h3>
          <p className="muted mono" style={{ marginTop: 2 }}>{n.kind} · {n.model}</p>
          <Markdown>{n.content_md}</Markdown>
        </div>
      ))}
      {refs.map((r) => (
        <div className="panel" key={r.id}>
          <h3 style={{ margin: 0 }}>★ {r.title}</h3>
          <p className="muted mono" style={{ marginTop: 2 }}>reference design · {r.model}</p>
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
