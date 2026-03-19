# Project Guidelines

## Code Style
- Follow the existing Python style in this repo: type hints where already used, straightforward functions and methods, and minimal inline comments.
- Keep edits small and local. Do not reformat unrelated files or rename public methods unless the task requires it.
- Match the surrounding module pattern before introducing new abstractions. This codebase favors direct procedural UI code in dialogs and mixin-based composition in the main app.

## Architecture
- This is a desktop Tkinter application. The entry point is `changsheng.py`, where `App` is assembled from many mixins.
- UI behavior is split across `app/mixins/`, `tabs/`, `dialogs/`, and `ui/`. Reuse existing helpers before adding new widget utilities.
- Persistence lives in `data/database_service.py` with SQLite. Business logic that affects invoices, payments, or outstanding balances must remain consistent with existing database APIs and tests.
- Cross-cutting concerns belong in `core/`, including logging, runtime behavior, config, and settings.

## Build And Test
- Use Python 3.10+ semantics.
- Run the app with `python changsheng.py`.
- Run the test suite with `python -m unittest discover tests`.
- When changing focused logic, run the most relevant tests first, then expand only if needed.

## Conventions
- Preserve bilingual UI behavior. If you add or change user-visible text, check whether it also needs to work with the translation flow in `data/language_map.py` or existing widget-tree translation helpers.
- For dialogs and tabs, preserve current Tkinter layout patterns, event bindings, and modal behavior unless the task explicitly changes UX behavior.
- For billing, invoice, payment, or outstanding-balance work, prefer fixing logic at the data or service layer instead of patching display-only symptoms.
- Keep database-related changes backward-compatible where possible and cover them with `tests/` updates.
- Prefer the existing `unittest` style used throughout `tests/` rather than introducing a different test framework or style in new tests.