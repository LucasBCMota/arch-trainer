import { marked } from "marked";
import Mermaid from "./Mermaid.jsx";

marked.setOptions({ gfm: true, breaks: false });

const MERMAID_FENCE = /```mermaid\s*([\s\S]*?)```/g;

// Renders Markdown, but turns ```mermaid fenced blocks into live diagrams.
// Single-user tool rendering your own model output / pasted notes — the trust
// boundary is yourself, so dangerouslySetInnerHTML is acceptable here.
export default function Markdown({ children }) {
  const src = children || "";
  const parts = [];
  let last = 0;
  let m;
  let i = 0;
  while ((m = MERMAID_FENCE.exec(src)) !== null) {
    if (m.index > last) {
      parts.push({ type: "md", content: src.slice(last, m.index) });
    }
    parts.push({ type: "mermaid", content: m[1] });
    last = m.index + m[0].length;
  }
  if (last < src.length) parts.push({ type: "md", content: src.slice(last) });

  return (
    <div className="markdown">
      {parts.map((p) =>
        p.type === "mermaid" ? (
          <Mermaid key={i++} chart={p.content} />
        ) : (
          <div key={i++} dangerouslySetInnerHTML={{ __html: marked.parse(p.content) }} />
        )
      )}
    </div>
  );
}
