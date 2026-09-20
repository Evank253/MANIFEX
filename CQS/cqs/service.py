"""CQS service facade."""

from __future__ import annotations
from dataclasses import replace
from .evidence import EvidenceStore
from .evaluator import evaluate
from .hashing import content_hash
from .ledger import QualificationLedger
from .models import Capability, EvidenceRecord, QualificationState
from .profiles import QualificationProfile, default_profiles


class CQSService:
    def __init__(self, profiles: dict[str, QualificationProfile] | None = None) -> None:
        self.profiles = profiles or default_profiles()
        self.capabilities: dict[tuple[str, str], Capability] = {}
        self.evidence = EvidenceStore()
        self.ledger = QualificationLedger()

    def register_capability(self, capability: Capability) -> Capability:
        key = (capability.capability_id, capability.version)
        if key in self.capabilities:
            raise ValueError("capability version already exists")
        if not capability.specification_hash:
            capability = replace(capability, specification_hash=content_hash(capability.identity_payload()))
        self.capabilities[key] = capability
        return capability

    def append_evidence(self, record: EvidenceRecord) -> EvidenceRecord:
        if (record.capability_id, record.capability_version) not in self.capabilities:
            raise KeyError("unknown capability version")
        return self.evidence.append(record)

    def qualify(self, capability_id: str, version: str):
        capability = self.capabilities[(capability_id, version)]
        profile = self.profiles[capability.qualification_profile]
        records = self.evidence.for_capability(capability_id, version)
        decision = evaluate(capability, profile, records)
        self.ledger.append(decision)
        return decision

    def availability(self, capability_id: str, version: str) -> bool:
        if not self.ledger.verify():
            raise RuntimeError("qualification ledger integrity failure")
        decisions = [
            e.decision for e in self.ledger.entries
            if e.decision.capability_id == capability_id
            and e.decision.capability_version == version
        ]
        return bool(decisions and decisions[-1].state == QualificationState.QUALIFIED)
