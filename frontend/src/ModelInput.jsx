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

// Free-text model entry + a saved list (synced to your account). Type any
// OpenRouter slug and Save it; ★ marks the default (moved to front, auto-selected);
// ✕ deletes one. The first saved model is the default.
export default function ModelInput({ value, onChange }) {
  const [models, setModels] = useState(null);
  const [saved, setSaved] = useState([]);

  useEffect(() => {
    api.models().then(setModels).catch(() => {});
    api
      .me()
      .then((m) => {
        const list = m.user?.favorite_models || [];
        setSaved(list);
        if (!localStorage.getItem(LS_KEY) && list.length) onChange(list[0]); // default = front
      })
      .catch(() => {});
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function persist(next) {
    const prev = saved;
    setSaved(next); // optimistic
    try {
      const res = await api.setFavoriteModels(next);
      setSaved(res.favorite_models);
    } catch {
      setSaved(prev); // revert
    }
  }

  const trimmed = (value || "").trim();

  function save() {
    if (!trimmed || saved.includes(trimmed)) return;
    persist([...saved, trimmed]);
  }
  function remove(m) {
    persist(saved.filter((x) => x !== m));
  }
  function makeDefault(m) {
    persist([m, ...saved.filter((x) => x !== m)]); // move to front
    onChange(m);
  }

  const suggestions = models
    ? Object.entries(models.suggested).flatMap(([prov, ids]) => ids.map((id) => `${prov}:${id}`))
    : [];
  const datalistOptions = [...new Set([...saved, ...suggestions])];

  return (
    <>
      <div className="row" style={{ alignItems: "stretch" }}>
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
        <button
          type="button"
          className="ghost"
          onClick={save}
          disabled={!trimmed || saved.includes(trimmed)}
          title="Save this model to your list"
        >
          Save
        </button>
      </div>
      <datalist id="model-suggestions">
        {datalistOptions.map((m) => (
          <option key={m} value={m} />
        ))}
      </datalist>

      {saved.length > 0 && (
        <ul className="model-list">
          {saved.map((m, i) => (
            <li key={m} className={value === m ? "on" : ""}>
              <button type="button" className="link" onClick={() => onChange(m)} title="Use this model">
                {i === 0 ? "★ " : ""}
                {m}
              </button>
              <span className="row" style={{ gap: 4 }}>
                {i !== 0 && (
                  <button
                    type="button"
                    className="iconbtn"
                    onClick={() => makeDefault(m)}
                    title="Make default"
                  >
                    ☆
                  </button>
                )}
                <button
                  type="button"
                  className="iconbtn"
                  onClick={() => remove(m)}
                  title="Delete"
                >
                  ✕
                </button>
              </span>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
