import unittest
from datetime import datetime, timedelta, timezone
from human_ai_companion.disclosure import SelectiveDisclosure
from human_ai_companion.models import ConsentGrant, Disclosure, EvidenceState, Provenance, Record, RecordKind, World


class DisclosureTests(unittest.TestCase):
    def record(self, rid, world=World.DEVELOPMENT):
        p = Provenance('source', 'rev', '0' * 64, datetime.now(timezone.utc).isoformat(), 'HUMAN')
        return Record(rid, 'p1', world, RecordKind.ARTIFACT, {}, EvidenceState.OBSERVED, p)

    def test_expired_consent_denies(self):
        from human_ai_companion.consent import ConsentManager
        cm = ConsentManager()
        cm.grant(ConsentGrant('c1', 'p1', World.DEVELOPMENT, World.PROFESSIONAL, (RecordKind.ARTIFACT,), 'portfolio', (datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat()))
        d = SelectiveDisclosure(cm)
        with self.assertRaises(PermissionError):
            d.prepare(Disclosure('d1','p1','employer',('r1',),'c1',datetime.now(timezone.utc).isoformat()), (self.record('r1'),))

    def test_unknown_record_is_rejected(self):
        from human_ai_companion.consent import ConsentManager
        cm = ConsentManager()
        cm.grant(ConsentGrant('c1', 'p1', World.DEVELOPMENT, World.PROFESSIONAL, (RecordKind.ARTIFACT,), 'portfolio'))
        d = SelectiveDisclosure(cm)
        with self.assertRaises(ValueError):
            d.prepare(Disclosure('d1','p1','employer',('missing',),'c1',datetime.now(timezone.utc).isoformat()), (self.record('r1'),))


if __name__ == '__main__':
    unittest.main()
