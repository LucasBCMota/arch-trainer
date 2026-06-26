import { useEffect, useState } from "react";
import { api } from "./api.js";

const LS_KEY = "arch.model";

// Remembers the chosen model string across views/reloads so you can switch on the
// fly without retyping. Empty string = use the server default (LLM_MODEL).
export function useModelSelection() {
  const [model, setModel] = useState(() => localStorage.getItem(LS_KEY) || "");
  const set = (v) => {
    setModel(v);
    if (v) localStorage.setItem(LS_KEY, v);
    else localStorage.removeItem(LS_KEY);
  };
  return [model, set];
}

// Free-text model entry with a datalist of suggestions. Type any OpenRouter slug
// (e.g. "openrouter:nvidia/nemotron-...:free") or pick a suggestion.
export default function ModelInput({ value, onChange }) {
  const [models, setModels] = useState(null);

  useEffect(() => {
    api.models().then(setModels).catch(() => {});
  }, []);

  const opts = models
    ? Object.entries(models.suggested).flatMap(([prov, ids]) => ids.map((id) => `${prov}:${id}`))
    : [];

  return (
    <>
      <input
        className="text-input"
        list="model-suggestions"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={models ? `default: ${models.current} — or type provider:model` : "provider:model_id"}
        spellCheck={false}
        autoCapitalize="off"
        autoCorrect="off"
      />
      <datalist id="model-suggestions">
        {opts.map((m) => (
          <option key={m} value={m} />
        ))}
      </datalist>
    </>
  );
}
