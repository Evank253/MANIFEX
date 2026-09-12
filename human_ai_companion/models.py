from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional


class World(str, Enum):
    PERSONAL = "PERSONAL"
    DEVELOPMENT = "DEVELOPMENT"
    PROFESSIONAL = "PROFESSIONAL"


class EvidenceState(str, Enum):
    REPORTED = "REPORTED"
    OBSERVED = "OBSERVED"
    ASSESSED = "ASSESSED"
    DEMONSTRATED = "DEMONSTRATED"
    VERIFIED = "VERIFIED"
    INDEPENDENTLY_VERIFIED = "INDEPENDENTLY_VERIFIED"
    HUMAN_CONFIRMED = "HUMAN_CONFIRMED"
    PROFESSIONAL_FINDING = "PROFESSIONAL_FINDING"


class RecordKind(str, Enum):
    MEMORY = "MEMORY"
    LEARNING_OBJECTIVE = "LEARNING_OBJECTIVE"
    ASSESSMENT = "ASSESSMENT"
    ATTEMPT = "ATTEMPT"
    ARTIFACT = "ARTIFACT"
    DEMONSTRATION = "DEMONSTRATION"
    CAPABILITY = "CAPABILITY"
    EVIDENCE = "EVIDENCE"
    CREDENTIAL = "CREDENTIAL"
    PORTFOLIO = "PORTFOLIO"
    PROGRESS = "PROGRESS"
    OPPORTUNITY = "OPPORTUNITY"
    CONSENT = "CONSENT"
    DISCLOSURE = "DISCLOSURE"
    PROFESSIONAL_PROFILE = "PROFESSIONAL_PROFILE"


@dataclass(frozen=True)
class Provenance:
    source_id: str
    source_revision: str
    content_sha256: str
    recorded_at: str
    actor: str


@dataclass(frozen=True)
class EvidenceRef:
    evidence_id: str
    state: EvidenceState
    artifact_id: Optional[str]
    provenance: Provenance
    verified_by: tuple[str, ...] = ()


@dataclass
class CapabilityRecord:
    capability_id: str
    name: str
    status: str
    evidence_ids: list[str] = field(default_factory=list)
    development_gap: Optional[str] = None
    strength_hypothesis: bool = False
    user_confirmed: bool = False


@dataclass(frozen=True)
class ConsentGrant:
    consent_id: str
    subject_id: str
    from_world: World
    to_world: World
    allowed_record_kinds: tuple[RecordKind, ...]
    purpose: str
    expires_at: Optional[str] = None
    revoked: bool = False


@dataclass(frozen=True)
class Disclosure:
    disclosure_id: str
    subject_id: str
    target: str
    record_ids: tuple[str, ...]
    consent_id: str
    created_at: str


@dataclass(frozen=True)
class HumanDecision:
    decision_id: str
    subject_id: str
    action: str
    authorized: bool
    decided_by: str
    rationale: Optional[str] = None


@dataclass(frozen=True)
class Record:
    record_id: str
    subject_id: str
    world: World
    kind: RecordKind
    payload: Mapping[str, Any]
    evidence_state: EvidenceState
    provenance: Provenance
