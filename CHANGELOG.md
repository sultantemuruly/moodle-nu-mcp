# Changelog

All notable changes to this project. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- `moodle_mcp/auth.py`: manual browser login via Playwright, session saved to `~/.config/moodle-mcp/storage_state.json`, validity check via `GET /my/`, and `session()` for reusing it headlessly.
- `moodle_mcp/config.py`: `BASE_URL` and session state path.
- `main.py`: dev CLI that runs any tool live (`courses`, `contents <id>`, `deadlines`, `materials <id>`, `download <id>`, ...), logging in first if needed.
- `moodle_mcp/client.py`: `MoodleClient` with `call()` (AJAX via `service.php` + `sesskey`) and `fetch_page()`, mapping Moodle errors to `SessionExpiredError` / `MoodleError`.
- `moodle_mcp/models.py`: frozen dataclasses for courses, sections, activities, deadlines, grades, materials, messages.
- `moodle_mcp/parsers.py`: selectolax parsers for folder pages, assignment status and the grade report.
- `moodle_mcp/tools/`: `courses` (list, contents via `core_courseformat_get_state`), `deadlines` (including overdue), `materials` (list + download to `~/Moodle/<course>/<section>/`, skipping existing files, links in `links.md`), `assignments`, `grades`, `messages`.
- `MoodleClient.download()` and `resolve_redirect()`.
- Tests for `auth`, `client`, parsers and tools.
- `docs/authentication.md`: implementation notes and live findings (no Microsoft redirect observed, cookie set, Moodle 5.1).
- `docs/data-access.md`: the cookie + `/lib/ajax/service.php` read model and the per-domain method list, verified live against NU.

### Changed
- `ruff` and `pytest` moved to dev dependencies.

## 2026-09-29 — Initial commit
- Project scaffold (`uv`, Python 3.13, Playwright), `docs/authentication.md`, `CLAUDE.md`.
