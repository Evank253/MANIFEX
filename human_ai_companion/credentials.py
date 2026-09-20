from dataclasses import dataclass
from hashlib import sha256
from .models import EvidenceState


@dataclass(frozen=True)
class Credential:
    credential_id: str
    subject_id: str
    title: str
    requirement_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    verification_ids: tuple[str, ...]
    issuer: str = "MANIFEX"
    status: str = "PENDING_HUMAN_REVIEW"

    def validate(self, evidence_states: dict[str, EvidenceState], requirements_passed: set[str], human_approved: bool = False) -> None:
        if not self.requirement_ids or not self.evidence_ids or not self.verification_ids:
            raise ValueError("credential requires requirements, evidence, and verification")
        if not set(self.requirement_ids).issubset(requirements_passed):
            raise ValueError("credential requirements are incomplete")
        for evidence_id in self.evidence_ids:
            if evidence_states.get(evidence_id) not in {EvidenceState.VERIFIED, EvidenceState.INDEPENDENTLY_VERIFIED, EvidenceState.HUMAN_CONFIRMED}:
                raise ValueError("credential evidence is not sufficiently verified")
        if not human_approved:
            raise PermissionError("credential issuance requires human approval")

    def digest(self) -> str:
        body = f"{self.credential_id}|{self.subject_id}|{self.title}|{self.requirement_ids}|{self.evidence_ids}|{self.verification_ids}|{self.issuer}"
        return sha256(body.encode()).hexdigest()
