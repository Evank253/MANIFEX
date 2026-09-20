"""Qualification evaluation. This module never mutates capability authority."""

from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from dataclasses import asdict
from .hashing import content_hash
from .models import Capability, QualificationDecision, QualificationState
from .profiles import QualificationProfile


def evaluate(
    capability: Capability,
    profile: QualificationProfile,
    evidence: list,
) -> QualificationDecision:
    ok, unmet, rationale = profile.evaluate(capability, evidence)
    state = QualificationState.QUALIFIED if ok else QualificationState.TESTED
    if any("SECURITY" in x for x in unmet):
        rationale.append("security evidence is missing or unusable")
    rationale.append("qualification is derived from preserved evidence")
    payload = {
        "capability": asdict(capability),
        "profile": profile.profile_id,
        "evidence_ids": sorted(e.evidence_id for e in evidence),
        "unmet": unmet,
        "state": state.value,
    }
    decision_hash = content_hash(payload)
    return QualificationDecision(
        decision_id=f"QD-{uuid4().hex[:12]}",
        capability_id=capability.capability_id,
        capability_version=capability.version,
        profile_id=profile.profile_id,
        state=state,
        evidence_ids=tuple(sorted(e.evidence_id for e in evidence)),
        unmet_requirements=tuple(unmet),
        rationale=tuple(rationale),
        decision_hash=decision_hash,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
