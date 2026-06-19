"""Swappable LLM provider layer.

Two real backends behind one `complete()` interface:
  - anthropic : the official `anthropic` SDK (never an OpenAI-compatible shim)
  - openai / openrouter : the `openai` SDK with a provider base_url

Model is selected by an "provider:model_id" string (env LLM_MODEL, optionally
overridden per request). API keys are read from env only — never the database.
"""

import json

from fastapi import HTTPException

from .config import settings

# Curated suggestions surfaced to the frontend model dropdown.
SUGGESTED_MODELS: dict[str, list[str]] = {
    "anthropic": ["claude-sonnet-4-6", "claude-opus-4-8", "claude-haiku-4-5"],
    "openrouter": ["anthropic/claude-3.5-sonnet", "openai/gpt-4o", "google/gemini-2.0-flash-001"],
    "openai": ["gpt-4o", "gpt-4o-mini"],
}

MAX_TOKENS = 8000


def _key_for(provider: str) -> str | None:
    return {
        "anthropic": settings.anthropic_api_key,
        "openai": settings.openai_api_key,
        "openrouter": settings.openrouter_api_key,
    }.get(provider)


def available_providers() -> list[str]:
    """Providers whose API key is present in env."""
    return [p for p in ("anthropic", "openai", "openrouter") if _key_for(p)]


def _split_model(model: str) -> tuple[str, str]:
    if ":" not in model:
        raise HTTPException(
            status_code=500,
            detail=f"LLM_MODEL must be 'provider:model_id', got {model!r}",
        )
    provider, model_id = model.split(":", 1)
    if provider not in SUGGESTED_MODELS:
        raise HTTPException(status_code=500, detail=f"Unknown provider {provider!r}")
    return provider, model_id


def _complete_anthropic(model_id: str, system: str, user: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    resp = client.messages.create(
        model=model_id,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in resp.content if b.type == "text")


def _complete_openai_compatible(
    provider: str, model_id: str, system: str, user: str
) -> str:
    from openai import OpenAI

    base_url = (
        settings.openrouter_base_url if provider == "openrouter" else settings.openai_base_url
    )
    client = OpenAI(api_key=_key_for(provider), base_url=base_url)
    resp = client.chat.completions.create(
        model=model_id,
        max_tokens=MAX_TOKENS,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content or ""


def complete(system: str, user: str, *, model: str | None = None) -> str:
    """Run one completion and return raw text."""
    model = model or settings.llm_model
    provider, model_id = _split_model(model)
    if not _key_for(provider):
        raise HTTPException(
            status_code=400,
            detail=f"No API key configured for provider {provider!r}. Set its *_API_KEY env var.",
        )
    if provider == "anthropic":
        return _complete_anthropic(model_id, system, user)
    return _complete_openai_compatible(provider, model_id, system, user)


def parse_model_json(text: str) -> dict:
    """Strip markdown fences the model sometimes adds, then json.loads.

    The model is instructed to emit raw JSON but occasionally wraps it in
    ```json ... ``` fences despite instructions — so we strip defensively and
    surface a clean 502 on failure.
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # drop the opening fence line (``` or ```json) and the trailing fence
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        if cleaned.rstrip().endswith("```"):
            cleaned = cleaned.rstrip()[: -len("```")]
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Model did not return valid JSON: {exc}. Raw start: {text[:200]!r}",
        ) from exc
