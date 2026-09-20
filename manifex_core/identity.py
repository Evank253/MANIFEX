from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionIdentity:
    subject: str
    manifest_id: str
    environment: str
    session_id: str

    def valid_for(self, subject: str, manifest_id: str, environment: str) -> bool:
        return (
            bool(self.subject)
            and self.subject == subject
            and self.manifest_id == manifest_id
            and self.environment == environment
            and bool(self.session_id)
        )
