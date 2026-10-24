from dataclasses import dataclass
from datetime import datetime, timezone

from .consent import ConsentManager
from .models import Disclosure, Record
from .privacy import PrivacyPolicy


@dataclass(frozen=True)
class DisclosureResult:
    disclosure: Disclosure
    records: tuple[Record, ...]


class SelectiveDisclosure:
    def __init__(self, consent: ConsentManager | None = None, privacy: PrivacyPolicy | None = None):
        self.consent = consent or ConsentManager()
        self.privacy = privacy or PrivacyPolicy()

    def prepare(self, disclosure: Disclosure, records: tuple[Record, ...]) -> DisclosureResult:
        if not disclosure.record_ids:
            raise ValueError('disclosure must contain records')
        if any(record.subject_id != disclosure.subject_id for record in records):
            raise PermissionError('disclosure contains records for another subject')
        by_id = {record.record_id: record for record in records}
        selected = tuple(by_id[rid] for rid in disclosure.record_ids if rid in by_id)
        if len(selected) != len(disclosure.record_ids):
            raise ValueError('disclosure references an unknown record')
        grant = self.consent._grants.get(disclosure.consent_id)
        if grant is None or grant.revoked:
            raise PermissionError('valid consent is required')
        if grant.subject_id != disclosure.subject_id:
            raise PermissionError('consent subject mismatch')
        if grant.expires_at:
            expiry = datetime.fromisoformat(grant.expires_at.replace('Z', '+00:00'))
            if expiry <= datetime.now(timezone.utc):
                raise PermissionError('consent has expired')
        for record in selected:
            if not self.privacy.can_disclose(record.world, grant.to_world, record.kind, grant):
                raise PermissionError(f'disclosure denied for {record.record_id}')
        return DisclosureResult(disclosure, selected)
