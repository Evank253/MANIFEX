"""Evidence-aware candidate comparison for MANIFEX."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .discovery import RepositoryInspection


@dataclass(frozen=True)
class CandidateScore:
    repository: str
    capability_match: float
    test_signal: float
    license_signal: float
    maintenance_signal: float
    popularity: int
    evidence_level: str = "NOT_MEASURED"

    @property
    def score(self) -> float:
        return round((self.capability_match * 0.40) + (self.test_signal * 0.25) +
                     (self.license_signal * 0.15) + (self.maintenance_signal * 0.20), 4)


class CandidateEvaluator:
    """Ranks candidates as decision support; ranking never grants verification."""

    def evaluate(self, inspection: RepositoryInspection, required_capabilities: Iterable[str]) -> CandidateScore:
        required = {x.lower() for x in required_capabilities}
        found = {x.lower() for x in inspection.capabilities}
        capability_match = len(required & found) / len(required) if required else 0.0
        test_signal = 1.0 if inspection.test_paths else 0.0
        license_signal = 0.0 if inspection.license_name == "NOT_MEASURED" else 1.0
        maintenance_signal = 1.0 if inspection.metadata.get("stars") is not None else 0.0
        return CandidateScore(
            repository=inspection.repository,
            capability_match=capability_match,
            test_signal=test_signal,
            license_signal=license_signal,
            maintenance_signal=maintenance_signal,
            popularity=int(inspection.metadata.get("stars", 0) or 0),
        )

    @staticmethod
    def rank(scores: Iterable[CandidateScore]) -> list[CandidateScore]:
        return sorted(scores, key=lambda x: (x.score, x.test_signal, x.license_signal), reverse=True)
