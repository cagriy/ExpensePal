# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
