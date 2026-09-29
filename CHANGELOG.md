# Changelog

All notable changes to this project. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- `moodle_mcp/auth.py`: manual browser login via Playwright, session saved to `~/.config/moodle-mcp/storage_state.json`, validity check via `GET /my/`, and `session()` for reusing it headlessly.
- `moodle_mcp/config.py`: `BASE_URL` and session state path.
- `main.py`: reuses a valid saved session, or opens the browser to log in.
- Tests for `auth` (`tests/test_auth.py`).
- `docs/authentication.md`: implementation notes and live findings (no Microsoft redirect observed, cookie set, Moodle 5.1).

### Changed
- `ruff` and `pytest` moved to dev dependencies.

## 2026-09-29 — Initial commit
- Project scaffold (`uv`, Python 3.13, Playwright), `docs/authentication.md`, `CLAUDE.md`.
