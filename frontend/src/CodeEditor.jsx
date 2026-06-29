import CodeMirror from "@uiw/react-codemirror";
import { oneDark } from "@codemirror/theme-one-dark";
import { python } from "@codemirror/lang-python";
import { javascript } from "@codemirror/lang-javascript";
import { java } from "@codemirror/lang-java";
import { cpp } from "@codemirror/lang-cpp";
import { go } from "@codemirror/lang-go";
import { rust } from "@codemirror/lang-rust";
import { sql } from "@codemirror/lang-sql";

// Heavy — imported lazily where used. Picks a syntax-highlighting extension by
// language name; unknown languages (or "any") just get a plain dark editor.
function extFor(language) {
  const l = (language || "").toLowerCase();
  if (l.includes("python")) return [python()];
  if (l.includes("typescript")) return [javascript({ jsx: true, typescript: true })];
  if (l.includes("javascript")) return [javascript({ jsx: true })];
  if (l.includes("java")) return [java()];
  if (l.includes("c++") || l === "cpp" || l === "c") return [cpp()];
  if (l.includes("go")) return [go()];
  if (l.includes("rust")) return [rust()];
  if (l.includes("sql")) return [sql()];
  return [];
}

export default function CodeEditor({ value, onChange, language, minHeight = 340 }) {
  return (
    <CodeMirror
      value={value}
      theme={oneDark}
      extensions={extFor(language)}
      onChange={onChange}
      minHeight={`${minHeight}px`}
      basicSetup={{ lineNumbers: true, highlightActiveLine: true }}
    />
  );
}
