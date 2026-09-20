from dataclasses import dataclass, field
from typing import Any

from .models import EvidenceRef


@dataclass
class HumanCapabilityPassport:
    subject_id: str
    credentials: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    assessments: list[str] = field(default_factory=list)
    demonstrations: list[str] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    work_experience: list[str] = field(default_factory=list)
    evidence: list[EvidenceRef] = field(default_factory=list)

    def export(self) -> dict[str, Any]:
        return {
            "format": "MANIFEX-HUMAN-CAPABILITY-PASSPORT/v1",
            "subject_id": self.subject_id,
            "credentials": list(self.credentials),
            "capabilities": list(self.capabilities),
            "assessments": list(self.assessments),
            "demonstrations": list(self.demonstrations),
            "projects": list(self.projects),
            "certifications": list(self.certifications),
            "work_experience": list(self.work_experience),
            "evidence": [
                {
                    "evidence_id": item.evidence_id,
                    "state": item.state.value,
                    "artifact_id": item.artifact_id,
                    "provenance": {
                        "source_id": item.provenance.source_id,
                        "source_revision": item.provenance.source_revision,
                        "content_sha256": item.provenance.content_sha256,
                        "recorded_at": item.provenance.recorded_at,
                        "actor": item.provenance.actor,
                    },
                }
                for item in self.evidence
            ],
        }
