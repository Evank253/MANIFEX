"""Domain-neutral qualification profile contract."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from .models import Capability, EvidenceRecord, EvidenceRequirement, EvidenceStatus


@dataclass(frozen=True)
class QualificationProfile:
    profile_id: str
    domain: str
    requirements: tuple[EvidenceRequirement, ...]

    def required_types(self) -> set[str]:
        return {r.evidence_type for r in self.requirements if r.required}

    def evaluate(self, capability: Capability, evidence: Iterable[EvidenceRecord]) -> tuple[bool, list[str], list[str]]:
        records = list(evidence)
        by_type: dict[str, list[EvidenceRecord]] = {}
        for record in records:
            by_type.setdefault(record.evidence_type, []).append(record)

        unmet: list[str] = []
        rationale: list[str] = []

        if not capability.name or not capability.capability_id or not capability.version:
            unmet.append("valid capability identity")
        else:
            rationale.append("capability identity is present")

        if not capability.specification_hash:
            unmet.append("specification_hash")
        else:
            rationale.append("specification identity is content-addressed")

        for req in self.requirements:
            matches = by_type.get(req.evidence_type, [])
            if not matches:
                if req.required:
                    unmet.append(req.evidence_type)
                continue
            usable = [m for m in matches if m.status == EvidenceStatus.PRESENT]
            if req.required and not usable:
                statuses = ",".join(sorted({m.status.value for m in matches}))
                unmet.append(f"{req.evidence_type} ({statuses})")
            elif usable:
                rationale.append(f"{req.evidence_type} evidence present")

        return not unmet, unmet, rationale


def default_profiles() -> dict[str, QualificationProfile]:
    common = (
        EvidenceRequirement("SPECIFICATION"),
        EvidenceRequirement("IMPLEMENTATION"),
        EvidenceRequirement("RUNTIME"),
        EvidenceRequirement("PERFORMANCE"),
        EvidenceRequirement("REPRODUCTION"),
        EvidenceRequirement("INDEPENDENCE"),
        EvidenceRequirement("VERIFICATION"),
    )
    return {
        "engineering.v1": QualificationProfile("engineering.v1", "engineering", common),
        "mathematical.v1": QualificationProfile(
            "mathematical.v1",
            "mathematics",
            common + (EvidenceRequirement("FORMAL_CORRECTNESS"),),
        ),
        "scientific.v1": QualificationProfile(
            "scientific.v1",
            "science",
            common + (EvidenceRequirement("EXPERIMENT"),),
        ),
        "educational.v1": QualificationProfile(
            "educational.v1",
            "education",
            common + (EvidenceRequirement("ASSESSMENT"),),
        ),
        "security.v1": QualificationProfile(
            "security.v1",
            "security",
            common + (EvidenceRequirement("SECURITY"),),
        ),
        "research.v1": QualificationProfile(
            "research.v1",
            "research",
            common,
        ),
    }
