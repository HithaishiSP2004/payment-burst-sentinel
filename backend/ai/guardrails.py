"""
Payment Burst Sentinel — AI Guardrails
========================================
Post-generation validation for AI investigation briefs.
7 guardrails to ensure safety, accuracy, and evidence grounding.
"""

import re
from typing import Optional
from .schemas import InvestigationBrief

# Prohibited fraud-certainty phrases
PROHIBITED_PHRASES = [
    "confirmed fraud",
    "is fraudulent",
    "committed fraud",
    "fraudster",
    "criminal activity",
    "definitely fraudulent",
    "proven fraud",
]

# Prohibited autonomous action phrases
PROHIBITED_ACTIONS = [
    "block payment",
    "block the payment",
    "freeze account",
    "freeze the account",
    "reject transaction",
    "reject the transaction",
    "ban merchant",
    "ban the merchant",
    "suspend merchant",
    "suspend the merchant",
]

# Output bounds
MAX_HEADLINE_LENGTH = 200
MAX_SUMMARY_LENGTH = 800
MAX_WHAT_CHANGED_ITEMS = 8
MAX_KEY_EVIDENCE_ITEMS = 8
MAX_INVESTIGATE_NEXT_ITEMS = 8
MAX_UNKNOWN_ITEMS = 8


def validate_brief(
    brief: InvestigationBrief,
    valid_evidence_ids: set[str],
) -> Optional[str]:
    """
    Validate an AI investigation brief against all 7 guardrails.

    Returns None if valid, or an error description if a guardrail fails.
    """

    # Guardrail 1 — Schema validation (already Pydantic-validated by this point)

    # Guardrail 2 — Evidence reference validation
    for claim in brief.what_changed:
        for eid in claim.evidence_ids:
            if eid not in valid_evidence_ids:
                return f"Invalid evidence reference '{eid}' in what_changed claim"

    for ke in brief.key_evidence:
        if ke.evidence_id not in valid_evidence_ids:
            return f"Invalid evidence reference '{ke.evidence_id}' in key_evidence"

    # Guardrail 3 — what_remains_unknown must be non-empty
    if not brief.what_remains_unknown:
        return "what_remains_unknown must not be empty"

    # Guardrail 4 — safety_note must be present and meaningful
    if not brief.safety_note or len(brief.safety_note.strip()) < 20:
        return "safety_note is missing or too short"

    # Guardrail 5 — Prohibited fraud certainty
    full_text = _flatten_text(brief)
    full_lower = full_text.lower()
    for phrase in PROHIBITED_PHRASES:
        if phrase in full_lower:
            return f"Prohibited fraud-certainty phrase detected: '{phrase}'"

    # Guardrail 6 — Autonomous action prohibition
    for phrase in PROHIBITED_ACTIONS:
        if phrase in full_lower:
            return f"Prohibited autonomous action detected: '{phrase}'"

    # Guardrail 7 — Output bounds
    if len(brief.headline) > MAX_HEADLINE_LENGTH:
        return f"Headline exceeds {MAX_HEADLINE_LENGTH} characters"
    if len(brief.summary) > MAX_SUMMARY_LENGTH:
        return f"Summary exceeds {MAX_SUMMARY_LENGTH} characters"
    if len(brief.what_changed) > MAX_WHAT_CHANGED_ITEMS:
        return f"what_changed exceeds {MAX_WHAT_CHANGED_ITEMS} items"
    if len(brief.key_evidence) > MAX_KEY_EVIDENCE_ITEMS:
        return f"key_evidence exceeds {MAX_KEY_EVIDENCE_ITEMS} items"
    if len(brief.investigate_next) > MAX_INVESTIGATE_NEXT_ITEMS:
        return f"investigate_next exceeds {MAX_INVESTIGATE_NEXT_ITEMS} items"
    if len(brief.what_remains_unknown) > MAX_UNKNOWN_ITEMS:
        return f"what_remains_unknown exceeds {MAX_UNKNOWN_ITEMS} items"

    return None  # All guardrails passed


def _flatten_text(brief: InvestigationBrief) -> str:
    """Flatten all text in a brief for content checks."""
    parts = [
        brief.headline,
        brief.summary,
        brief.safety_note,
    ]
    for c in brief.what_changed:
        parts.append(c.statement)
    for ke in brief.key_evidence:
        parts.append(ke.observation)
        parts.append(ke.why_it_matters)
    parts.extend(brief.investigate_next)
    parts.extend(brief.what_remains_unknown)
    return " ".join(parts)
