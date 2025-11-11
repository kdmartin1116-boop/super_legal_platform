# External Repo Integration Plan

Source: https://github.com/MrNAM205/Sovereign-Instrument-Endorsement-Discharging-Engine

Goal: Reuse UI components and AI prompt patterns from the external repo to accelerate frontend demo features and improve our server-side prompt templates.

Scope of this initial integration:
- Extracted prompt templates into `backend/modules/prompt_templates.py` (this commit).

Candidate components to reuse:
- UI: `components/CreditDispute.tsx`, `FlowDiagram.tsx`, `EndorsementModal.tsx`, `ModuleCard.tsx` — adapt for our frontend.
- Prompts: affidavit generation, credit analysis, endorsement explanations — moved to server-side templates.
- Config: `vite.config.ts` and README usage for a quick demo setup.

Integration tasks (concrete):
1. Audit licenses and confirm compatibility.
2. Add prompt templates to backend (done for initial set).
3. Create adapters in `backend/modules/document_processing.py` to call `get_prompt` and supply document text/analysis.
4. Create minimal API endpoint `POST /api/v1/prompts/render` (optional) to test server-side prompt rendering.
5. Import or re-implement selected React components in our frontend; adapt props to call our endpoints.
6. Add tests for prompt rendering and a small E2E demo that uploads a sample file and uses the new prompts.
7. Create branch, PR, and document changes.

Acceptance criteria:
- Server-side prompt templates are present and unit-tested.
- A demo page or component calls the backend to get rendered prompt outputs.
- License compatibility confirmed.

Notes:
- The external repo is frontend-focused and calls Google GenAI client-side. For security, move AI calls to server-side and protect keys.
