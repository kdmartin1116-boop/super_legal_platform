"""Quick script to validate prompt templates import and formatting."""
import sys
import os

# ensure repo root is on sys.path so we can import backend packages
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.modules.prompt_templates import get_prompt

def _main():
    # Basic smoke tests
    p1 = get_prompt('credit_analysis')
    assert '{document_text}' in p1
    print('credit_analysis template loaded OK')

    p2 = get_prompt('affidavit_generation')
    assert '{analysis}' in p2
    print('affidavit_generation template loaded OK')

    p3 = get_prompt('endorsement_explanation')
    rendered = p3.format(endorsement_type='Qualified')
    assert 'Qualified' in rendered
    print('endorsement_explanation template renders OK')

    print('All prompt smoke checks passed')

if __name__ == '__main__':
    _main()
