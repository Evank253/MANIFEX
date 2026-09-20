from .models import ConsentGrant, Disclosure, RecordKind, World
from .privacy import PrivacyPolicy


class ConsentManager:
    def __init__(self, privacy: PrivacyPolicy | None = None) -> None:
        self.privacy = privacy or PrivacyPolicy()
        self._grants: dict[str, ConsentGrant] = {}

    def grant(self, consent: ConsentGrant) -> None:
        if consent.revoked:
            raise ValueError("cannot register revoked consent")
        self._grants[consent.consent_id] = consent

    def revoke(self, consent_id: str) -> ConsentGrant:
        current = self._grants[consent_id]
        revoked = ConsentGrant(current.consent_id, current.subject_id, current.from_world, current.to_world, current.allowed_record_kinds, current.purpose, current.expires_at, True)
        self._grants[consent_id] = revoked
        return revoked

    def can_share(self, consent_id: str, subject_id: str, from_world: World, to_world: World, kind: RecordKind) -> bool:
        consent = self._grants.get(consent_id)
        if consent is None or consent.subject_id != subject_id:
            return False
        return self.privacy.can_disclose(from_world, to_world, kind, consent)

    def require_share(self, disclosure: Disclosure, records: list[tuple[World, RecordKind]]) -> None:
        consent = self._grants.get(disclosure.consent_id)
        if consent is None:
            raise PermissionError("no consent exists")
        self.privacy.authorize_disclosure(disclosure, records, consent)
