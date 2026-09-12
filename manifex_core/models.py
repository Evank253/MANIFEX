from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def now() -> datetime:
    return datetime.now(timezone.utc)

class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"
    UNKNOWN = "UNKNOWN"

class SecurityState(str, Enum):
    CREATED="CREATED"; ATTESTING="ATTESTING"; AUTHORIZED="AUTHORIZED"; SANDBOXED="SANDBOXED"; RUNNING="RUNNING"; MONITORED="MONITORED"; VERIFYING="VERIFYING"; CLOSED="CLOSED"; DENIED="DENIED"; BLOCKED="BLOCKED"; QUARANTINED="QUARANTINED"; REVOKED="REVOKED"; TERMINATED="TERMINATED"; FAILED="FAILED"; UNKNOWN="UNKNOWN"

@dataclass(frozen=True)
class Authorization:
    id: str
    subject: str
    issuer: str
    human_authority: str
    action: str
    purpose: str
    capabilities: frozenset[str]
    resources: frozenset[str] = frozenset()
    data_scope: frozenset[str] = frozenset()
    network_scope: frozenset[str] = frozenset()
    environment: str = "sandbox"
    risk_level: str = "LOW"
    issued_at: datetime = field(default_factory=now)
    expires_at: datetime = field(default_factory=now)
    revocable: bool = True
    status: str = "ACTIVE"
    approval: str | None = None

    def valid(self, at: datetime | None = None) -> bool:
        at = at or now()
        return self.status == "ACTIVE" and self.issued_at <= at < self.expires_at and bool(self.human_authority) and bool(self.approval)

@dataclass(frozen=True)
class CapabilityLease:
    id: str
    authorization_id: str
    subject: str
    capabilities: frozenset[str]
    issued_at: datetime
    expires_at: datetime
    revoked: bool = False

    def valid(self, at: datetime | None = None) -> bool:
        at = at or now()
        return not self.revoked and self.issued_at <= at < self.expires_at and bool(self.capabilities)

@dataclass(frozen=True)
class OperationRequest:
    request_id: str
    actor: str
    action: str
    purpose: str
    requested_capabilities: frozenset[str]
    resources: frozenset[str] = frozenset()
    network_scope: frozenset[str] = frozenset()
    risk_level: str = "LOW"
    consequential: bool = True
    human_approval: str | None = None

@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    event_type: str
    timestamp: datetime
    actor: str
    request_id: str | None
    authorization_id: str | None
    capability_lease_id: str | None
    action: str
    state_before: str | None
    state_after: str | None
    decision: str | None
    result: str | None
    reason: str | None
    input_hash: str | None
    output_hash: str | None
    constitution_hash: str
    previous_event_hash: str
    event_hash: str
    evidence_refs: tuple[str, ...] = ()

@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    evidence_type: str
    artifact_hash: str
    source_hash: str
    test_hash: str
    environment_hash: str
    produced_by: str
    independently_verified: bool
    status: str
    created_at: datetime = field(default_factory=now)

@dataclass(frozen=True)
class DecisionRecord:
    request_id: str
    decision: Decision
    reason: str
    invariants: tuple[str, ...]
    authorization_id: str | None = None
    lease_id: str | None = None
