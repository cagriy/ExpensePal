# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-02-20

### Changed
- Moved receipt extraction prompts from Python module to `prompts/receipt_extraction.md`
- Scanner now reads and parses prompts from the markdown file at runtime
- Switched default model to `claude-haiku-4-5-20251001`

### Added
- Prompt logging: full system and user prompts are saved to `logs/<timestamp>_prompt.txt` before each LLM call
