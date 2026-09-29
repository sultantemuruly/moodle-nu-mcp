# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

An MCP server that exposes NU Moodle (`https://moodle.nu.edu.kz`) to AI agents. Python 3.13, managed with `uv`, using Playwright for browser automation.

Read [docs/authentication.md](docs/authentication.md) before touching anything auth-related. The main constraint: NU Moodle logs in through Microsoft Entra ID (`auth_oauth2`), so `/login/token.php` username/password exchange **cannot work**. Authenticated access reuses a real browser session: Playwright runs a manual Microsoft login, then saves `storage_state` holding the `MoodleSession` cookie. Write requests also need the `sesskey` CSRF token.

## Commands

```bash
uv sync                           # install deps into .venv
uv run playwright install chromium  # one-time browser download
uv run python main.py             # run the entry point
uv add <pkg> / uv add --dev <pkg> # add dependencies (never pip install)

uv run ruff check --fix . && uv run ruff format .  # lint + format
uv run pytest                                      # all tests
uv run pytest tests/test_x.py::test_name           # single test
```

Type checking is configured for pyright/basedpyright (`pyrightconfig.json`, `[tool.pyright]`).

Test what you write. Every behavior change comes with a pytest test. Before you call work done, run ruff and the relevant tests, and make sure they pass. Keep `tests/` mirroring the module layout. Mock Moodle at the `client` boundary so tests never need a live login.

## Architecture

Organize code into modules with one responsibility each. That way a task can go to one module, and an agent can work on it after reading only that module and the interfaces it imports. Dependencies point one way, top to bottom:

| Layer | Responsibility | May import |
|-------|----------------|------------|
| `server` | MCP server setup, registers tools | `tools` |
| `tools/` | One file per domain (courses, assignments, grades, …); thin MCP tool functions that validate input and shape output | `client`, `models` |
| `client` | All HTTP/Playwright interaction with Moodle (page fetches, AJAX `service.php` calls, `sesskey` handling) | `auth`, `models` |
| `auth` | Obtain, persist, validate, and refresh the browser session | `config` |
| `models` | Typed data structures (dataclasses / TypedDicts) shared across layers | — |
| `config` | Constants: `BASE_URL`, session state path | — |

All modules live in the `moodle_mcp/` package; `main.py` is a thin runnable entry point. Implemented so far: `config`, `auth`.

Rules:
- Only `client` talks to Moodle; only `auth` knows how sessions are stored. Tools never touch Playwright or raw HTTP directly.
- No circular imports and no reaching across layers. If two modules need the same thing, move it down a layer.
- Each module exposes a small public surface. Prefix internal helpers with `_`.
- When adding a module or changing a layer boundary, update the table above.

## Coding style

Aim for clear, elegant code, and the fewest lines that still work correctly and read clearly.

- Use full type hints everywhere. Code must pass pyright with no errors. Use modern syntax: `list[str]`, `X | None`, `match`, dataclasses.
- Write small, pure functions. Compose them instead of branching deeply. Use early returns instead of nested `if`s.
- Don't add speculative abstractions, wrapper classes around a single function, or config for things that don't vary. Three similar lines beat a premature helper.
- Delete dead code rather than commenting it out. Don't keep backward-compat shims in this young codebase.
- Comments explain *why* (Moodle quirks, auth constraints). Never restate *what* the code does. Keep docstrings to one line unless an MCP tool needs a fuller description for the agent.
- Fail loudly with specific exceptions. Catch only where you can recover or add context. No bare `except`.
- Async by default for I/O (Playwright async API, async MCP handlers). Don't mix sync and async Playwright.
- Constants such as the base URL live in one place and are never duplicated.

## CHANGELOG.md — keep in sync

Every user-visible or architectural change adds a line under `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md), in the same change as the code. Use the sections Added / Changed / Fixed / Removed. Write one line per change that says what changed, not how. Skip pure refactors and formatting.

## Secrets — check before every commit

Before any commit, check the staged files for credentials: passwords, tokens (`wstoken`), cookies or `MoodleSession` values, `sesskey`, `.env` files, and saved Playwright session state. If any such file or value is present and not gitignored, **do not commit**. Stop and tell the user right away what you found and where. Don't silently add it to `.gitignore` and carry on.

## docs/ — keep in sync

`docs/` holds research findings about Moodle's behavior: auth flow, endpoints, web-service functions, page structures and quirks. Treat it as part of the codebase:

- When you discover something non-obvious about Moodle (an endpoint, a required parameter, a response shape, a limitation), record it in the relevant `docs/*.md`, or create a new topic file for a new area.
- When code changes invalidate something in `docs/`, fix the doc in the same change. Stale docs are bugs.
- Docs record findings and evidence (what was observed and where), not code walkthroughs.
- Link to the relevant doc from the module that depends on it.
