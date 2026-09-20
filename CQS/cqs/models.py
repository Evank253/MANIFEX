"""Core CQS records.

Historical records are immutable dataclasses. Derived qualification/availability
state is produced by evaluation and must not mutate historical evidence.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class QualificationState(str, Enum):
    PROPOSED = "PROPOSED"
    SPECIFIED = "SPECIFIED"
    IMPLEMENTED = "IMPLEMENTED"
    TESTED = "TESTED"
    BENCHMARKED = "BENCHMARKED"
    SECURITY_REVIEWED = "SECURITY_REVIEWED"
    REPRODUCED = "REPRODUCED"
    INDEPENDENTLY_VERIFIED = "INDEPENDENTLY_VERIFIED"
    QUALIFIED = "QUALIFIED"
    AVAILABLE = "AVAILABLE"


class EvidenceStatus(str, Enum):
    PRESENT = "PRESENT"
    NOT_MEASURED = "NOT_MEASURED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"


@dataclass(frozen=True)
class EvidenceRequirement:
    evidence_type: str
    required: bool = True


@dataclass(frozen=True)
class Capability:
    capability_id: str
    version: str
    schema_version: str
    domain: str
    name: str
    description: str
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    prerequisites: dict[str, tuple[str, ...]] = field(default_factory=dict)
    mechanism: dict[str, Any] = field(default_factory=dict)
    implementation: dict[str, Any] = field(default_factory=dict)
    execution: dict[str, Any] = field(default_factory=dict)
    qualification_profile: str = ""
    specification_hash: str = ""
    mechanism_hash: str = ""
    implementation_hash: str = ""

    def identity_payload(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "version": self.version,
            "schema_version": self.schema_version,
            "domain": self.domain,
            "name": self.name,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "prerequisites": self.prerequisites,
            "mechanism": self.mechanism,
            "implementation": self.implementation,
        }


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    capability_id: str
    capability_version: str
    evidence_type: str
    status: EvidenceStatus
    producer: str
    content_hash: str
    provenance: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    observations: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class QualificationDecision:
    decision_id: str
    capability_id: str
    capability_version: str
    profile_id: str
    state: QualificationState
    evidence_ids: tuple[str, ...]
    unmet_requirements: tuple[str, ...]
    rationale: tuple[str, ...]
    decision_hash: str
    evaluated_at: str
