# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Added
- Server-side prompt templates (credit_analysis, affidavit_generation, endorsement_explanation, instrument_parse) — `backend/modules/prompt_templates.py`
- `DocumentProcessingService.render_prompt` and `render_prompt_with_analysis` adapter to render templates using stored analysis — `backend/modules/document_processing.py`
- API endpoint `POST /api/v1/documents/prompts/render` to render server-side prompts — `backend/api/document_processing.py`
- Unit tests for prompt templates and adapter — `tests/test_prompt_templates.py`, `tests/test_prompt_adapter.py`
- CI workflow to run prompt smoke checks and pytest — `.github/workflows/prompt-check.yml`
- Frontend demo scaffold demonstrating prompt rendering calls (`frontend/demo`) with `CreditDispute` and `FlowDiagram` components.
- Smoke-check script `scripts/check_prompts.py` for quick local validation

### Changed
- Integrated external prompt patterns and UI inspiration from the Sovereign Instrument frontend to centralize AI prompt logic on the server and provide a demo scaffold.

### Notes
- For security, AI model calls should run server-side; the demo calls the server endpoint which enforces authentication in production.
- To run tests locally, install dev dependencies: `pip install -r requirements-dev.txt` and run `python -m pytest`.
