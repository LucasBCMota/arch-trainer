import { lazy, Suspense, useRef, useState } from "react";
import { api } from "../api.js";
import Markdown from "../Markdown.jsx";
import Mermaid from "../Mermaid.jsx";
import MermaidBuilder from "../MermaidBuilder.jsx";
import Tabs from "../Tabs.jsx";

const ExcalidrawCanvas = lazy(() => import("../ExcalidrawCanvas.jsx"));
const CodeEditor = lazy(() => import("../CodeEditor.jsx"));

function buildTemplate(scenario) {
  const tpl = scenario.response_template;
  if (tpl?.length) {
    return tpl
      .map((s) => `## ${s.section}\n${s.guidance ? `<!-- ${s.guidance} -->\n` : ""}`)
      .join("\n");
  }
  return "";
}

export default function Answering({ scenario, onResult, onCancel }) {
  const structured = scenario.exercise_type === "structured";
  const isCode = scenario.exercise_type === "language" || scenario.exercise_type === "algorithms";
  const [answer, setAnswer] = useState(() => buildTemplate(scenario));
  const [tab, setTab] = useState("write");
  // Captured in a ref (NOT state) so Excalidraw's frequent onChange never
  // triggers a re-render loop (React error #185).
  const freehandRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function submit() {
    setLoading(true);
    setError(null);
    try {
      const pending = await api.createSession({
        scenario_id: scenario.id,
        user_answer: answer,
        answer_freehand: freehandRef.current,
      });
      const ready = await api.poll(() => api.getSession(pending.id), {
        where: "the Dashboard session log",
      });
      onResult(ready);
    } catch (e) {
      setError(e.message);
      setLoading(false);
    }
  }

  const placeholder = structured
    ? "Fill in each section. Put your architecture in a ```mermaid block under Diagram."
    : "Walk through your design: key decisions, tradeoffs, failure modes, open questions…";

  const answerTabs = [
    { key: "write", label: "Write" },
    { key: "preview", label: "Preview" },
    { key: "diagram", label: "Diagram builder", hidden: isCode },
    { key: "freehand", label: "Freehand", hidden: isCode },
  ];

  if (loading) {
    return (
      <div className="panel" style={{ textAlign: "center", padding: "48px 22px" }}>
        <div className="spinner" />
        <h2 style={{ marginTop: 16 }}>Judging your answer…</h2>
        <p className="muted">
          Queued to the model. This can take a few minutes on slow/free models — keep this tab open;
          your result will appear automatically.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="panel">
        <div className="muted" style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: "0.06em" }}>
          {scenario.difficulty}-level · {scenario.focus_area}
          {structured ? " · structured" : ""}
          {scenario.language ? ` · ${scenario.language}` : ""}
        </div>
        <h3 style={{ margin: "6px 0 8px", fontSize: 21 }}>{scenario.title}</h3>
        <p className="muted">{scenario.context}</p>
        <p>
          <strong>Problem.</strong> {scenario.problem}
        </p>
        {scenario.context_diagram && (
          <>
            <label className="field" style={{ marginTop: 14 }}>Given system</label>
            <Mermaid chart={scenario.context_diagram} />
          </>
        )}
        {scenario.constraints?.length > 0 && (
          <>
            <label className="field" style={{ marginTop: 14 }}>
              {structured ? "Requirements" : "Constraints"}
            </label>
            <ul className="constraints">
              {scenario.constraints.map((c, i) => (
                <li key={i}>{c}</li>
              ))}
            </ul>
          </>
        )}
      </div>

      <div className="panel">
        <h2 style={{ marginBottom: 8 }}>Your answer</h2>
        <Tabs tabs={answerTabs} active={tab} onChange={setTab} />

        <div style={{ display: tab === "write" ? "block" : "none" }}>
          {isCode ? (
            <Suspense fallback={<textarea value={answer} onChange={(e) => setAnswer(e.target.value)} />}>
              <CodeEditor value={answer} onChange={setAnswer} language={scenario.language} />
            </Suspense>
          ) : (
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder={placeholder}
              autoFocus
            />
          )}
        </div>

        {tab === "preview" && (
          <div className="preview">
            <Markdown>{answer}</Markdown>
          </div>
        )}

        {!isCode && tab === "diagram" && (
          <MermaidBuilder
            onInsert={(code) => {
              setAnswer((a) => `${a.trimEnd()}\n\n\`\`\`mermaid\n${code}\n\`\`\`\n`);
              setTab("write");
            }}
          />
        )}

        {!isCode && tab === "freehand" && (
          <div>
            <p className="muted" style={{ fontSize: 13 }}>
              Optional sketchpad to think — <b>not graded</b>, but saved next to the reference diagram
              on the result screen. The graded diagram is the Mermaid in your answer.
            </p>
            <Suspense fallback={<p className="muted">Loading canvas…</p>}>
              <ExcalidrawCanvas
                initialData={freehandRef.current}
                onScene={(s) => (freehandRef.current = s)}
              />
            </Suspense>
          </div>
        )}

        <div className="row" style={{ marginTop: 16 }}>
          <button className="primary" onClick={submit} disabled={loading || !answer.trim()}>
            Submit for judgment
          </button>
          <button className="ghost" onClick={onCancel}>
            Cancel
          </button>
        </div>
        {error && <p className="error" style={{ marginTop: 12 }}>{error}</p>}
      </div>
    </>
  );
}
