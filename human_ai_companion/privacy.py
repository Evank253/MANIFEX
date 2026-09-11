from dataclasses import dataclass
from .models import ConsentGrant, Disclosure, RecordKind, World


@dataclass(frozen=True)
class PrivacyPolicy:
    """Deny cross-world disclosure unless an explicit consent grant permits it."""

    def can_disclose(self, record_world: World, target_world: World, kind: RecordKind, consent: ConsentGrant | None) -> bool:
        if record_world == target_world:
            return True
        if consent is None or consent.revoked:
            return False
        if consent.from_world != record_world or consent.to_world != target_world:
            return False
        return kind in consent.allowed_record_kinds

    def authorize_disclosure(self, disclosure: Disclosure, records: list[tuple[World, RecordKind]], consent: ConsentGrant) -> None:
        if disclosure.consent_id != consent.consent_id or consent.subject_id != disclosure.subject_id:
            raise PermissionError("disclosure is not bound to the supplied consent")
        for world, kind in records:
            if not self.can_disclose(world, World.PROFESSIONAL, kind, consent):
                raise PermissionError(f"professional disclosure denied for {world.value}/{kind.value}")
