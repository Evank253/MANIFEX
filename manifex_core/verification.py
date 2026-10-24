"""Verification integration point for MANIFEX engineering gates."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class VerificationResult:
    status: str
    passed: bool
    gates: Mapping[str, bool]
    evidence_level: str
    notes: str = ""


class VerificationEngine:
    """Aggregates executable gate results; it never fabricates missing evidence."""

    def evaluate(self, gates: Mapping[str, bool], *, evidence_level: str = "NOT_MEASURED") -> VerificationResult:
        normalized = dict(gates)
        passed = bool(normalized) and all(normalized.values())
        status = "VERIFIED" if passed else ("BLOCKED" if not normalized else "FAILED")
        return VerificationResult(status, passed, normalized, evidence_level,
                                  "All supplied gates passed." if passed else "One or more required gates are missing or failed.")
