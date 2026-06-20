import { useEffect, useState } from "react";
import { api } from "../api.js";
import Markdown from "../Markdown.jsx";

function ModelPicker({ models, value, onChange }) {
  if (!models) return null;
  const opts = Object.entries(models.suggested).flatMap(([prov, ids]) =>
    ids.map((id) => `${prov}:${id}`)
  );
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)} style={{ maxWidth: 320 }}>
      <option value="">default ({models.current})</option>
      {opts.map((m) => (
        <option key={m} value={m}>
          {m}
        </option>
      ))}
    </select>
  );
}

export default function Study() {
  const [gaps, setGaps] = useState([]);
  const [notes, setNotes] = useState([]);
  const [models, setModels] = useState(null);
  const [model, setModel] = useState("");
  const [topic, setTopic] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [open, setOpen] = useState(null); // note being read
  const [showImport, setShowImport] = useState(false);

  function load() {
    api.studyNotes("?kind=deep_dive").then(setNotes).catch((e) => setError(e.message));
  }
  useEffect(() => {
    load();
    api.patternGaps().then((g) => setGaps(g.slice(0, 8))).catch(() => {});
    api.models().then(setModels).catch(() => {});
  }, []);

  async function generate(t) {
    if (!t.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const note = await api.study(t, model);
      setNotes((n) => [note, ...n]);
      setOpen(note);
      setTopic("");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function remove(id) {
    await api.deleteNote(id).catch(() => {});
    setNotes((n) => n.filter((x) => x.id !== id));
    if (open?.id === id) setOpen(null);
  }
  async function togglePin(note) {
    const updated = await api.pinNote(note.id, !note.pinned);
    setNotes((n) => n.map((x) => (x.id === note.id ? updated : x)));
    if (open?.id === note.id) setOpen(updated);
  }

  if (open) {
    return (
      <NoteReader
        note={open}
        onBack={() => setOpen(null)}
        onDelete={() => remove(open.id)}
        onPin={() => togglePin(open)}
        onSaved={(u) => {
          setNotes((n) => n.map((x) => (x.id === u.id ? u : x)));
          setOpen(u);
        }}
      />
    );
  }

  return (
    <>
      <div className="panel">
        <h2>Study a pattern</h2>
        <p className="muted" style={{ marginTop: -6 }}>
          Generate a deep-dive on any pattern, or one you keep missing. Pages are stored — generate
          once with a strong model, read forever.
        </p>
        <label className="field">Model</label>
        <ModelPicker models={models} value={model} onChange={setModel} />
        <div className="row" style={{ marginTop: 14 }}>
          <input
            className="text-input"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. compare-and-delete / optimistic locking"
            onKeyDown={(e) => e.key === "Enter" && generate(topic)}
          />
          <button className="primary" disabled={busy || !topic.trim()} onClick={() => generate(topic)}>
            {busy ? "Generating…" : "Generate"}
          </button>
          <button className="ghost" onClick={() => setShowImport((s) => !s)}>
            {showImport ? "Close import" : "Paste / import"}
          </button>
        </div>
        {error && <p className="error" style={{ marginTop: 10 }}>{error}</p>}

        {showImport && (
          <ImportForm
            kind="deep_dive"
            onSaved={(note) => {
              setNotes((n) => [note, ...n]);
              setShowImport(false);
              setOpen(note);
            }}
          />
        )}
      </div>

      {gaps.length > 0 && (
        <div className="panel">
          <h2>Study your gaps</h2>
          <div className="chips">
            {gaps.map((g) => (
              <button
                key={g.pattern_name}
                className="chip"
                disabled={busy}
                onClick={() => generate(g.pattern_name)}
                title={`Missed ${g.count}×`}
              >
                {g.pattern_name} · {g.count}×
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="panel">
        <h2>Study library</h2>
        {notes.length === 0 ? (
          <p className="muted">No study notes yet.</p>
        ) : (
          <ul className="note-list">
            {notes.map((n) => (
              <li key={n.id}>
                <button className="link" onClick={() => setOpen(n)}>
                  {n.pinned ? "★ " : ""}
                  {n.topic}
                </button>
                <span className="muted mono"> · {n.model}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
}

function NoteReader({ note, onBack, onDelete, onPin, onSaved }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(note.content_md);
  const [topic, setTopic] = useState(note.topic);

  async function save() {
    const u = await api.updateNote(note.id, { topic, content_md: draft });
    onSaved(u);
    setEditing(false);
  }

  return (
    <div className="panel">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <button className="ghost" onClick={onBack}>
          ← back
        </button>
        <div className="row">
          <button className="ghost" onClick={onPin}>
            {note.pinned ? "★ pinned" : "☆ pin"}
          </button>
          <button className="ghost" onClick={() => setEditing((e) => !e)}>
            {editing ? "cancel" : "edit"}
          </button>
          <button className="ghost" onClick={onDelete}>
            delete
          </button>
        </div>
      </div>
      {editing ? (
        <>
          <input
            className="text-input"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            style={{ marginTop: 12 }}
          />
          <textarea value={draft} onChange={(e) => setDraft(e.target.value)} style={{ marginTop: 10 }} />
          <button className="primary" style={{ marginTop: 10 }} onClick={save}>
            Save
          </button>
        </>
      ) : (
        <>
          <h2 style={{ marginTop: 14 }}>{note.topic}</h2>
          <p className="muted mono" style={{ marginTop: -8 }}>
            {note.kind} · {note.model}
          </p>
          <Markdown>{note.content_md}</Markdown>
        </>
      )}
    </div>
  );
}

export function ImportForm({ kind, onSaved }) {
  const [topic, setTopic] = useState("");
  const [content, setContent] = useState("");
  const [source, setSource] = useState("claude.ai");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function save() {
    setBusy(true);
    setError(null);
    try {
      const note = await api.importNote({ topic, kind, content_md: content, source });
      onSaved(note);
      setTopic("");
      setContent("");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ marginTop: 16, borderTop: "1px solid var(--border)", paddingTop: 16 }}>
      <label className="field">Import Markdown (generated elsewhere — no tokens spent)</label>
      <div className="row" style={{ marginBottom: 10 }}>
        <input
          className="text-input"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Topic / pattern name"
        />
        <input
          className="text-input"
          value={source}
          onChange={(e) => setSource(e.target.value)}
          placeholder="source label"
          style={{ maxWidth: 160 }}
        />
      </div>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Paste Markdown here…"
      />
      <button
        className="primary"
        style={{ marginTop: 10 }}
        disabled={busy || !topic.trim() || !content.trim()}
        onClick={save}
      >
        {busy ? "Saving…" : "Import"}
      </button>
      {error && <p className="error" style={{ marginTop: 10 }}>{error}</p>}
    </div>
  );
}
