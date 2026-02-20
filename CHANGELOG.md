# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.4] - 2026-02-20

### Changed
- Default model switched from `claude-haiku-4-5-20251001` to `claude-opus-4-6`

## [0.1.3] - 2026-02-20

### Added
- `multi-scan` command for batch receipt processing from a folder
- `web_review.py`: `review_receipts_batch()` — persistent Flask server with three-column UI (file list sidebar, image/PDF preview, editable form)
- Confirmed receipts are moved to `<folder>/done/` automatically; skipped files stay in the list
- Server shuts down automatically when all files are confirmed or the user clicks Quit

## [0.1.2] - 2026-02-20

### Changed
- Replaced Textual TUI with a local web UI for receipt review (Flask)
- Receipt image and editable fields now displayed side-by-side in the browser
- PDF receipts rendered via embedded iframe in the review form

### Added
- `web_review.py`: Flask-based review server with confirm/cancel flow

### Removed
- `tui.py` and `textual` dependency

## [0.1.1] - 2026-02-20

### Changed
- Moved receipt extraction prompts from Python module to `prompts/receipt_extraction.md`
- Scanner now reads and parses prompts from the markdown file at runtime
- Switched default model to `claude-haiku-4-5-20251001`

### Added
- Prompt logging: full system and user prompts are saved to `logs/<timestamp>_prompt.txt` before each LLM call
