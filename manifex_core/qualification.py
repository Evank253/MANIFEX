"""Evidence-aware qualification decisions for discovered assets."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QualificationDecision:
    approved: bool
    state: str
    reason: str


class QualificationEngine:
    """Does not infer trust from discovery, metadata, or popularity."""

    def decide(self, *, state: str, evidence_level: str, verification_status: str,
               license_known: bool, tests_passed: bool) -> QualificationDecision:
        if state == "DISCOVERED":
            return QualificationDecision(False, "DISCOVERED", "Discovery alone is not qualification.")
        if evidence_level == "NOT_MEASURED":
            return QualificationDecision(False, state, "Evidence remains NOT_MEASURED.")
        if not license_known:
            return QualificationDecision(False, state, "License compatibility is not established.")
        if not tests_passed or verification_status != "VERIFIED":
            return QualificationDecision(False, state, "Executable verification is not established.")
        return QualificationDecision(True, "REUSABLE", "Required qualification evidence is present.")
