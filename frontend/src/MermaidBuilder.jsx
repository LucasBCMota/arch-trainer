import { useMemo, useState } from "react";
import Mermaid from "./Mermaid.jsx";

// Strip characters that would break Mermaid node/edge syntax.
const clean = (s) =>
  (s || "")
    .replace(/["[\]{}|<>]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

function nextId(nodes) {
  const max = nodes.reduce((m, n) => {
    const num = parseInt(String(n.id).replace(/\D/g, ""), 10);
    return Number.isFinite(num) && num > m ? num : m;
  }, 0);
  return `n${max + 1}`;
}

// Block-based Mermaid builder: add nodes, connect them with edges, pick a
// direction → generates valid `flowchart` Mermaid with a live preview, instead
// of hand-writing syntax. `onInsert(code)` drops it into the answer.
export default function MermaidBuilder({ onInsert }) {
  const [direction, setDirection] = useState("TD");
  const [nodes, setNodes] = useState([
    { id: "n1", label: "Client" },
    { id: "n2", label: "API" },
  ]);
  const [edges, setEdges] = useState([{ from: "n1", to: "n2", label: "" }]);

  function addNode() {
    setNodes((ns) => [...ns, { id: nextId(ns), label: "Node" }]);
  }
  function setNodeLabel(id, label) {
    setNodes((ns) => ns.map((n) => (n.id === id ? { ...n, label } : n)));
  }
  function removeNode(id) {
    setNodes((ns) => ns.filter((n) => n.id !== id));
    setEdges((es) => es.filter((e) => e.from !== id && e.to !== id));
  }
  function addEdge() {
    setEdges((es) => [...es, { from: nodes[0]?.id || "", to: nodes[0]?.id || "", label: "" }]);
  }
  function setEdge(i, patch) {
    setEdges((es) => es.map((e, j) => (j === i ? { ...e, ...patch } : e)));
  }
  function removeEdge(i) {
    setEdges((es) => es.filter((_, j) => j !== i));
  }

  const code = useMemo(() => {
    const lines = [`flowchart ${direction}`];
    nodes.forEach((n) => lines.push(`  ${n.id}["${clean(n.label) || n.id}"]`));
    edges.forEach((e) => {
      if (!e.from || !e.to) return;
      const lbl = clean(e.label);
      lines.push(lbl ? `  ${e.from} -->|${lbl}| ${e.to}` : `  ${e.from} --> ${e.to}`);
    });
    return lines.join("\n");
  }, [direction, nodes, edges]);

  const nodeLabel = (id) => {
    const n = nodes.find((x) => x.id === id);
    return n ? `${n.id}: ${n.label}` : id;
  };

  return (
    <div className="builder">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div className="row">
          <span className="muted" style={{ fontSize: 13 }}>Direction:</span>
          {["TD", "LR"].map((d) => (
            <button key={d} className={`chip ${direction === d ? "on" : ""}`} onClick={() => setDirection(d)}>
              {d === "TD" ? "top-down" : "left-right"}
            </button>
          ))}
        </div>
        <button className="primary" onClick={() => onInsert(code)}>
          Insert into answer
        </button>
      </div>

      <div className="builder-cols">
        <div>
          <label className="field">Nodes</label>
          {nodes.map((n) => (
            <div className="row" key={n.id} style={{ marginBottom: 6 }}>
              <span className="mono muted" style={{ minWidth: 28 }}>{n.id}</span>
              <input
                className="text-input"
                value={n.label}
                onChange={(e) => setNodeLabel(n.id, e.target.value)}
              />
              <button className="iconbtn" onClick={() => removeNode(n.id)} title="Remove">✕</button>
            </div>
          ))}
          <button className="ghost" onClick={addNode}>+ node</button>

          <label className="field" style={{ marginTop: 14 }}>Connections</label>
          {edges.map((e, i) => (
            <div className="row" key={i} style={{ marginBottom: 6, flexWrap: "nowrap" }}>
              <select value={e.from} onChange={(ev) => setEdge(i, { from: ev.target.value })}>
                {nodes.map((n) => <option key={n.id} value={n.id}>{nodeLabel(n.id)}</option>)}
              </select>
              <span className="muted">→</span>
              <select value={e.to} onChange={(ev) => setEdge(i, { to: ev.target.value })}>
                {nodes.map((n) => <option key={n.id} value={n.id}>{nodeLabel(n.id)}</option>)}
              </select>
              <input
                className="text-input"
                style={{ maxWidth: 110 }}
                placeholder="label"
                value={e.label}
                onChange={(ev) => setEdge(i, { label: ev.target.value })}
              />
              <button className="iconbtn" onClick={() => removeEdge(i)} title="Remove">✕</button>
            </div>
          ))}
          <button className="ghost" onClick={addEdge} disabled={nodes.length === 0}>+ connection</button>
        </div>

        <div>
          <label className="field">Preview</label>
          <Mermaid chart={code} />
        </div>
      </div>
    </div>
  );
}
