from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable, Mapping


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class QualificationState(str, Enum):
    DISCOVERED = "DISCOVERED"
    EXTRACTED = "EXTRACTED"
    REPRODUCED = "REPRODUCED"
    BENCHMARKED = "BENCHMARKED"
    SECURITY_TESTED = "SECURITY_TESTED"
    VERIFIED = "VERIFIED"
    QUALIFIED = "QUALIFIED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    NOT_MEASURED = "NOT_MEASURED"
    QUARANTINED = "QUARANTINED"


QUALIFICATION_ORDER = {
    QualificationState.DISCOVERED: 0,
    QualificationState.EXTRACTED: 1,
    QualificationState.REPRODUCED: 2,
    QualificationState.BENCHMARKED: 3,
    QualificationState.SECURITY_TESTED: 4,
    QualificationState.VERIFIED: 5,
    QualificationState.QUALIFIED: 6,
}


class QualificationError(ValueError):
    pass


@dataclass(frozen=True)
class Provenance:
    source: str
    repository: str | None = None
    commit: str | None = None
    tree_hash: str | None = None
    license: str | None = None


@dataclass(frozen=True)
class EvidenceReference:
    evidence_id: str
    evidence_type: str
    artifact_hash: str
    test_hash: str
    independently_verified: bool = False


@dataclass(frozen=True)
class BenchmarkResult:
    benchmark_id: str
    benchmark_version: str
    metric: str
    value: float
    conditions_hash: str
    raw_result_hash: str
    reproduced: bool = False
    independently_verified: bool = False


@dataclass
class CapabilityGenome:
    id: str
    name: str
    category: str
    function: str
    mechanism: str
    inputs: frozenset[str] = frozenset()
    outputs: frozenset[str] = frozenset()
    dependencies: frozenset[str] = frozenset()
    required_models: frozenset[str] = frozenset()
    required_tools: frozenset[str] = frozenset()
    required_resources: frozenset[str] = frozenset()
    required_privileges: frozenset[str] = frozenset()
    network_requirements: frozenset[str] = frozenset()
    filesystem_requirements: frozenset[str] = frozenset()
    provenance: Provenance | None = None
    evidence: tuple[EvidenceReference, ...] = ()
    benchmarks: tuple[BenchmarkResult, ...] = ()
    threat_model: str | None = None
    attack_surface: frozenset[str] = frozenset()
    sandbox_requirements: frozenset[str] = frozenset()
    credential_requirements: frozenset[str] = frozenset()
    known_vulnerabilities: tuple[str, ...] = ()
    qualification: QualificationState = QualificationState.DISCOVERED
    created_at: datetime = field(default_factory=utc_now)
    last_transition_at: datetime = field(default_factory=utc_now)

    @property
    def qualified(self) -> bool:
        return self.qualification is QualificationState.QUALIFIED

    def can_execute(self) -> bool:
        return self.qualified

    def add_evidence(self, evidence: EvidenceReference) -> None:
        self.evidence = (*self.evidence, evidence)

    def add_benchmark(self, benchmark: BenchmarkResult) -> None:
        self.benchmarks = (*self.benchmarks, benchmark)

    def transition(self, target: QualificationState, *, evidence: Iterable[EvidenceReference] = ()) -> None:
        allowed = {
            QualificationState.DISCOVERED: {QualificationState.EXTRACTED, QualificationState.BLOCKED, QualificationState.FAILED, QualificationState.NOT_MEASURED, QualificationState.QUARANTINED},
            QualificationState.EXTRACTED: {QualificationState.REPRODUCED, QualificationState.BLOCKED, QualificationState.FAILED, QualificationState.NOT_MEASURED, QualificationState.QUARANTINED},
            QualificationState.REPRODUCED: {QualificationState.BENCHMARKED, QualificationState.BLOCKED, QualificationState.FAILED, QualificationState.NOT_MEASURED, QualificationState.QUARANTINED},
            QualificationState.BENCHMARKED: {QualificationState.SECURITY_TESTED, QualificationState.BLOCKED, QualificationState.FAILED, QualificationState.NOT_MEASURED, QualificationState.QUARANTINED},
            QualificationState.SECURITY_TESTED: {QualificationState.VERIFIED, QualificationState.BLOCKED, QualificationState.FAILED, QualificationState.NOT_MEASURED, QualificationState.QUARANTINED},
            QualificationState.VERIFIED: {QualificationState.QUALIFIED, QualificationState.BLOCKED, QualificationState.FAILED, QualificationState.NOT_MEASURED, QualificationState.QUARANTINED},
            QualificationState.QUALIFIED: {QualificationState.BLOCKED, QualificationState.QUARANTINED},
            QualificationState.FAILED: {QualificationState.REPRODUCED, QualificationState.BLOCKED, QualificationState.QUARANTINED},
            QualificationState.BLOCKED: {QualificationState.DISCOVERED, QualificationState.QUARANTINED},
            QualificationState.NOT_MEASURED: {QualificationState.EXTRACTED, QualificationState.BLOCKED, QualificationState.QUARANTINED},
            QualificationState.QUARANTINED: {QualificationState.DISCOVERED, QualificationState.BLOCKED},
        }
        if target not in allowed[self.qualification]:
            raise QualificationError(
                f"invalid qualification transition: {self.qualification.value} -> {target.value}"
            )
        if target is QualificationState.QUALIFIED:
            if not self.provenance:
                raise QualificationError("qualification requires provenance")
            if not self.evidence:
                raise QualificationError("qualification requires evidence")
            if not any(e.independently_verified for e in self.evidence):
                raise QualificationError("qualification requires independently verified evidence")
            if not self.benchmarks:
                raise QualificationError("qualification requires benchmark evidence")
            if not any(b.reproduced and b.independently_verified for b in self.benchmarks):
                raise QualificationError("qualification requires reproduced and independently verified benchmark evidence")
            if self.known_vulnerabilities:
                raise QualificationError("qualification blocked by known vulnerabilities")
        self.evidence = (*self.evidence, *tuple(evidence))
        self.qualification = target
        self.last_transition_at = utc_now()


@dataclass(frozen=True)
class CapabilityRequirement:
    capability_ids: frozenset[str] = frozenset()
    categories: frozenset[str] = frozenset()
    required_privileges: frozenset[str] = frozenset()


@dataclass
class CapabilityRegistry:
    _capabilities: dict[str, CapabilityGenome] = field(default_factory=dict)

    def register(self, capability: CapabilityGenome) -> None:
        if capability.id in self._capabilities:
            raise ValueError(f"capability already registered: {capability.id}")
        self._capabilities[capability.id] = capability

    def get(self, capability_id: str) -> CapabilityGenome:
        return self._capabilities[capability_id]

    def all(self) -> tuple[CapabilityGenome, ...]:
        return tuple(self._capabilities.values())

    def qualified(self) -> tuple[CapabilityGenome, ...]:
        return tuple(c for c in self._capabilities.values() if c.qualified)

    def available(self, requirement: CapabilityRequirement) -> tuple[CapabilityGenome, ...]:
        candidates = [c for c in self._capabilities.values() if c.qualified]
        if requirement.capability_ids:
            candidates = [c for c in candidates if c.id in requirement.capability_ids]
        if requirement.categories:
            candidates = [c for c in candidates if c.category in requirement.categories]
        if requirement.required_privileges:
            candidates = [
                c for c in candidates
                if requirement.required_privileges.issubset(c.required_privileges)
            ]
        return tuple(candidates)


@dataclass(frozen=True)
class EvidencePackage:
    capability_id: str
    qualification: QualificationState
    provenance_present: bool
    evidence_ids: tuple[str, ...]
    benchmark_ids: tuple[str, ...]
    independent_verification: bool
    generated_at: datetime = field(default_factory=utc_now)

    @property
    def sufficient_for_qualification(self) -> bool:
        return (
            self.qualification is QualificationState.QUALIFIED
            and self.provenance_present
            and bool(self.evidence_ids)
            and bool(self.benchmark_ids)
            and self.independent_verification
        )


def build_evidence_package(capability: CapabilityGenome) -> EvidencePackage:
    return EvidencePackage(
        capability_id=capability.id,
        qualification=capability.qualification,
        provenance_present=capability.provenance is not None,
        evidence_ids=tuple(e.evidence_id for e in capability.evidence),
        benchmark_ids=tuple(b.benchmark_id for b in capability.benchmarks),
        independent_verification=(
            any(e.independently_verified for e in capability.evidence)
            and any(b.reproduced and b.independently_verified for b in capability.benchmarks)
        ),
    )


@dataclass(frozen=True)
class IntelligenceProfile:
    breadth: float | None = None
    depth: float | None = None
    reasoning: float | None = None
    problem_solving: float | None = None
    research: float | None = None
    retrieval: float | None = None
    tool_use: float | None = None
    engineering: float | None = None
    creative_generation: float | None = None
    cross_domain_transfer: float | None = None
    learning: float | None = None
    self_critique: float | None = None
    verification: float | None = None
    reproducibility: float | None = None

    def as_dict(self) -> Mapping[str, float | None]:
        return self.__dict__.copy()
