# AGENTS.md

## Cursor Cloud specific instructions

### Overview

**agent-cli-to-api** is a Python FastAPI gateway that exposes agent CLIs (Codex, Cursor Agent, Claude Code, Gemini) as an OpenAI-compatible HTTP API (`/v1/*`). It is a single-process Python application with no Docker, database, or external infrastructure dependencies.

### Running the application

```bash
# Start with any provider (codex, gemini, claude, cursor-agent)
uv run agent-cli-to-api codex --host 127.0.0.1 --port 8000

# Doctor diagnostic (checks CLI backends availability)
uv run agent-cli-to-api doctor
```

The server binds to `127.0.0.1:8000` by default. Key endpoints: `GET /healthz`, `GET /v1/models`, `POST /v1/chat/completions`, `GET /debug/config`.

### Caveats

- **No dedicated test suite exists** in the repository. Validation is done via `py_compile` for syntax checking and the `scripts/smoke.sh` script against a running server.
- **No linting config** is included in `pyproject.toml`. Use `ruff check codex_gateway/` for basic linting (install via `uv tool install ruff`).
- **Backend CLIs are required** for actual request proxying. Without an authenticated CLI (codex, claude, gemini, or cursor-agent), the gateway starts but returns errors on `/v1/chat/completions`. The `/healthz`, `/v1/models`, and `/debug/config` endpoints work without any backend.
- The gateway does **not** load `.env` by default. Use `--env-file .env` or `--auto-env` to load one.
- `uv sync` is the canonical dependency install command (see `README.md`).
