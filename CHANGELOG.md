# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.7] - 2026-02-21

### Added
- `--train` flag for `multi-scan`: adds an inline prompt editor to the web UI so users can tweak the extraction prompt, re-process a receipt with the modified prompt, and save it back to disk without leaving the browser
- `prompt_template_override` parameter on `scan_receipt()` to use a custom prompt template string instead of reading from disk
- `/save-prompt` POST endpoint (only active in train mode) that writes the edited template back to `expense_pal/prompts/receipt_extraction.md`

## [0.1.6] - 2026-02-21

### Added
- `sync-descriptions` command: fetches up to 200 expense descriptions from FreeAgent and saves them to a local file
- LLM-powered description recommendations: the receipt extraction prompt now includes known descriptions and instructs Claude to reuse or create a concise one
- Custom autocomplete dropdown for the description field in both single-scan and multi-scan UIs, with full color control (replaces native `<datalist>`)
- `load_descriptions()` and `save_description()` helpers in `config.py`; new descriptions are auto-appended on confirm

### Changed
- Description field is now pre-filled with the LLM's suggestion; clicking selects all text so typing immediately replaces it
- `max_tokens` increased from 512 to 1024 in `scan_receipt()` to accommodate the description field
- `scan_receipt()` return dict now includes a `description` key

## [0.1.5] - 2026-02-20

### Added
- Model dropdown in multi-scan UI (Haiku / Sonnet / Opus); defaults to Sonnet
- Server-side scan result cache — navigating back to a file loads instantly without a new LLM call
- Re-process button to force a re-scan with the currently selected model
- `/reprocess/<filename>` POST endpoint that clears the cache entry and re-scans

### Changed
- `scan_receipt()` accepts an optional `model` parameter overriding the default from env
- Cache is cleared for a file when it is confirmed and moved to `done/`

### Removed
- Skip button and `/skip` endpoint from multi-scan UI

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
