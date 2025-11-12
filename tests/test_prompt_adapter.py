import sys
import os
import pytest
import asyncio

# ensure repo root on path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.modules.document_processing import DocumentProcessingService
from types import SimpleNamespace


class DummyAsyncSession:
    def __init__(self, document=None, analysis=None, issues=None, remedies=None):
        self._doc = document
        self._analysis = analysis
        self._issues = issues or []
        self._remedies = remedies or []

    async def get(self, model, id_):
        # Return document record stub
        return self._doc

    async def execute(self, query):
        # Very small shim: return object with scalar_one_or_none and scalars
        class Result:
            def __init__(self, value):
                self._value = value

            def scalar_one_or_none(self):
                return self._value

            def scalars(self):
                return SimpleNamespace(all=lambda: self._value if isinstance(self._value, list) else [self._value])

        # determine which select is being requested by looking for attributes
        # We'll inspect for the presence of 'analysis_id' in query string repr as heuristic
        q = repr(query)
        if 'AnalysisResultRecord' in q:
            return Result(self._analysis)
        if 'LegalIssueRecord' in q:
            return Result(self._issues)
        if 'RemedyRecord' in q:
            return Result(self._remedies)
        return Result(None)


@pytest.mark.asyncio
async def test_render_prompt_with_no_analysis(monkeypatch):
    service = DocumentProcessingService()

    # create a minimal document stub
    doc = SimpleNamespace(id='doc-1', text_content='This is a test document.', uploaded_by='user-1')

    db = DummyAsyncSession(document=doc)

    # monkeypatch render_prompt to avoid template formatting complexities
    def fake_render(name, context=None):
        return f"RENDERED:{name}:{context.get('document_text')[:10]}"

    service.render_prompt = fake_render

    rendered = await service.render_prompt_with_analysis('doc-1', 'user-1', db, 'credit_analysis')
    assert rendered.startswith('RENDERED:credit_analysis:')


@pytest.mark.asyncio
async def test_render_prompt_with_analysis_and_issues(monkeypatch):
    service = DocumentProcessingService()

    # create document and analysis stubs
    doc = SimpleNamespace(id='doc-2', text_content='Agreement between A and B', uploaded_by='user-2')
    analysis = SimpleNamespace(id='analysis-1', document_type='contract', confidence_score=0.87, processing_time=1.23)
    issue = SimpleNamespace(id='i1', title='Contradiction', severity='high', description='Conflicting clause', confidence=0.9)
    remedy = SimpleNamespace(id='r1', title='Add termination clause', category='contract', priority='high', implementation_steps_json='["Add clause"]')

    db = DummyAsyncSession(document=doc, analysis=analysis, issues=[issue], remedies=[remedy])

    # Use real render_prompt from templates but override get_prompt to a simple one
    monkeypatch.setattr('backend.modules.prompt_templates.TEMPLATES', {'simple': 'Doc:{document_text}\nIssues:{issues}\nRemedies:{remedies}'})

    rendered = await service.render_prompt_with_analysis('doc-2', 'user-2', db, 'simple')
    assert 'Agreement between A' in rendered
    assert 'Contradiction' in rendered
    assert 'Add termination clause' in rendered or 'Add clause' in rendered
