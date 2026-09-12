from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping

from .models import EvidenceState, Provenance, EvidenceRef


@dataclass(frozen=True)
class EvidenceChain:
    claim_id: str
    assessment_id: str
    raw_result_id: str
    artifact_id: str
    verification_id: str
    provenance: Provenance
    credential_id: str | None = None

    def validate(self) -> None:
        required = (self.claim_id, self.assessment_id, self.raw_result_id, self.artifact_id, self.verification_id)
        if not all(required):
            raise ValueError("evidence chain contains an unbound stage")
        if not self.provenance.content_sha256:
            raise ValueError("evidence chain requires content provenance")


def artifact_sha256(content: bytes) -> str:
    return sha256(content).hexdigest()


def make_evidence_ref(evidence_id: str, state: EvidenceState, artifact_id: str | None, provenance: Provenance) -> EvidenceRef:
    if state in {EvidenceState.VERIFIED, EvidenceState.INDEPENDENTLY_VERIFIED} and artifact_id is None:
        raise ValueError("verified evidence requires an artifact reference")
    return EvidenceRef(evidence_id=evidence_id, state=state, artifact_id=artifact_id, provenance=provenance)


def verify_artifact_digest(content: bytes, expected_sha256: str) -> bool:
    return artifact_sha256(content) == expected_sha256
