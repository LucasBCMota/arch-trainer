# Architecture Trainer — Claude Instructions

## Stack
- Backend: FastAPI + SQLAlchemy + Postgres, deps managed with `uv`
- Frontend: React (Vite)
- Deploy: Render (web service + managed Postgres), defined via `render.yaml`
- AI: Anthropic API (claude-sonnet-4-6), called server-side only — never expose the key to the frontend

## Memory Files

This project uses `.claude.md` files to track decisions, discoveries, and context that would otherwise require re-exploring the codebase. These files are gitignored and are for Claude's use only.

### Root-level architecture memory: `architecture.claude.md`

There is a single `architecture.claude.md` at the repo root that is the source of truth for overall architecture and planning decisions. **After completing any task that involves an architectural decision, new pattern, or planning change, update this file.** It should always reflect the current state of the project.

What belongs here:
- Overall system design and tech stack choices
- Key architectural decisions and why they were made
- Patterns used across the codebase
- Planned or in-progress major changes

### Local `.claude.md` files

Create a `<topic>.claude.md` file in the most relevant directory when you discover something non-obvious or make a decision scoped to that area.

What belongs here:
- Why a specific decision was made in that module
- Non-obvious gotchas (e.g., "the judging prompt expects the candidate's answer last in the user message — moving it changes scoring behavior")
- Tradeoffs considered and rejected
- Local patterns that deviate from framework defaults

### General rules
- Before exploring the codebase, check for `.claude.md` files in the relevant directories first.
- Keep entries concise — bullet points or short paragraphs. Not documentation, just enough to avoid re-deriving the same thing.
- Update stale entries after refactors or decision changes.
- Do NOT record things obvious from reading the code or already in official docs.

## AI Prompt Changes

The scenario-generation and judging prompts are the core of this tool's value. If you change either:
- Note the change and why in `architecture.claude.md` under a "Prompt history" section
- Don't silently change the expected JSON shape without updating both the Pydantic response models and the frontend parsing

## Git Commits
- Commit messages must be a **single concise line** (conventional commit style: `feat:`, `fix:`, `chore:`, etc.)
- **NEVER** add `Co-Authored-By: Claude` or any co-author trailer
- **NEVER** add the "Generated with Claude Code" footer
