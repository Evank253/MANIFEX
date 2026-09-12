import pytest

from human_ai_companion.companion import HumanAICompanion
from human_ai_companion.models import ConsentGrant, EvidenceState, HumanDecision, Provenance, Record, RecordKind, World
from human_ai_companion.privacy import PrivacyPolicy


P = Provenance("test", "rev-1", "abc", "2026-01-01T00:00:00Z", "HUMAN")


def test_personal_record_stays_personal_without_consent():
    companion = HumanAICompanion("u1")
    companion.record(Record("m1", "u1", World.PERSONAL, RecordKind.MEMORY, {}, EvidenceState.REPORTED, P))
    consent = None
    assert not PrivacyPolicy().can_disclose(World.PERSONAL, World.PROFESSIONAL, RecordKind.MEMORY, consent)


def test_explicit_consent_can_disclose_allowed_kind():
    consent = ConsentGrant("c1", "u1", World.DEVELOPMENT, World.PROFESSIONAL, (RecordKind.ASSESSMENT,), "job application")
    assert PrivacyPolicy().can_disclose(World.DEVELOPMENT, World.PROFESSIONAL, RecordKind.ASSESSMENT, consent)
    assert not PrivacyPolicy().can_disclose(World.DEVELOPMENT, World.PROFESSIONAL, RecordKind.MEMORY, consent)


def test_consequential_action_requires_human():
    companion = HumanAICompanion("u1")
    with pytest.raises(PermissionError):
        companion.authorize_consequential_action(HumanDecision("d1", "u1", "HIRE", True, "META"))
    companion.authorize_consequential_action(HumanDecision("d2", "u1", "HIRE", True, "HUMAN"))


def test_verified_evidence_requires_artifact():
    from human_ai_companion.evidence import make_evidence_ref
    with pytest.raises(ValueError):
        make_evidence_ref("e1", EvidenceState.VERIFIED, None, P)


def test_subject_isolation():
    companion = HumanAICompanion("u1")
    with pytest.raises(PermissionError):
        companion.record(Record("m2", "u2", World.PERSONAL, RecordKind.MEMORY, {}, EvidenceState.REPORTED, P))
