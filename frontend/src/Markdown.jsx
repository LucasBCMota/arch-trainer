import { marked } from "marked";

marked.setOptions({ gfm: true, breaks: false });

// Single-user tool rendering your own model output / pasted notes — the trust
// boundary is yourself, so dangerouslySetInnerHTML is acceptable here.
export default function Markdown({ children }) {
  return (
    <div
      className="markdown"
      dangerouslySetInnerHTML={{ __html: marked.parse(children || "") }}
    />
  );
}
