import sys
import os

# Ensure repo root on path for imports
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.modules.prompt_templates import get_prompt


def test_credit_analysis_template_contains_placeholders():
    tmpl = get_prompt('credit_analysis')
    assert '{document_text}' in tmpl
    assert '{previous_analysis}' in tmpl


def test_affidavit_template_contains_analysis_placeholder():
    tmpl = get_prompt('affidavit_generation')
    assert '{analysis}' in tmpl


def test_endorsement_template_renders():
    tmpl = get_prompt('endorsement_explanation')
    rendered = tmpl.format(endorsement_type='Qualified')
    assert 'Qualified' in rendered
