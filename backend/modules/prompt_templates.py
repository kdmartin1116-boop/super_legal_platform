"""
Prompt templates harvested from the Sovereign Instrument frontend repo
Purpose: provide server-side templates for document analysis, affidavit generation,
and endorsement explanation. These are initial, audited copies intended to be
adapted and tested further.

Usage:
    from backend.modules.prompt_templates import get_prompt
    prompt = get_prompt('credit_analysis').format(...)
"""
from typing import Dict

TEMPLATES: Dict[str, str] = {
    # Credit report analysis — identify inaccuracies and suggest dispute steps
    "credit_analysis": (
        "You are an expert in sovereign law, the UCC, and credit reporting laws like the FCRA. "
        "Analyze the following credit report document. Identify potential inaccuracies, "
        "unverifiable items, and opportunities for lawful dispute. For each item you identify, "
        "explain the basis for the dispute from a sovereign perspective and suggest a brief course of action. "
        "Format your response in clear, actionable markdown.\n\nPREVIOUS ANALYSIS:\n---\n{previous_analysis}\n\nDOCUMENT:\n---\n{document_text}"
    ),

    # Affidavit generation — produce a formal affidavit of truth based on analysis
    "affidavit_generation": (
        "Based on the original credit report and the following analysis, draft a formal, legally structured "
        "Affidavit of Truth. The affidavit should clearly state the identified inaccuracies as facts asserted by the affiant. "
        "It should be written from a sovereign perspective, ready for the user to copy, notarize, and send as a lawful dispute instrument. "
        "Do not include placeholder brackets for personal info like name or address; instead, use placeholders like [Your Name] or [Your Address].\n\nANALYSIS:\n---\n{analysis}" 
    ),

    # Endorsement explanation prompt (used in frontend for UCC endorsements)
    "endorsement_explanation": (
        "Explain a '{endorsement_type}' endorsement on a negotiable instrument according to the UCC. "
        "What are its implications? Explain it clearly and concisely for someone studying sovereign remedy. "
        "Provide an example of wording and short notes on legal effects and limits."
    ),

    # Generic instrument parsing hint
    "instrument_parse": (
        "Parse the following instrument text. Identify instrument type (order vs bearer), parties, amounts, payment dates, "
        "endorsement lines, and any clauses that could create contradictions or ambiguity. Return a structured JSON summary.\n\n{document_text}"
    ),
}


def get_prompt(name: str) -> str:
    """Return the named prompt template.

    Raise KeyError if not present.
    """
    return TEMPLATES[name]
