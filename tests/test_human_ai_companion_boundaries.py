from human_ai_companion.models import ConsentGrant, EvidenceState, RecordKind, World
from human_ai_companion.privacy import PrivacyPolicy


def test_personal_to_professional_is_denied_by_default():
    assert not PrivacyPolicy().can_disclose(World.PERSONAL, World.PROFESSIONAL, RecordKind.MEMORY, None)


def test_development_to_professional_requires_allowed_consent():
    consent = ConsentGrant("c", "u", World.DEVELOPMENT, World.PROFESSIONAL, (RecordKind.ASSESSMENT,), "application")
    policy = PrivacyPolicy()
    assert policy.can_disclose(World.DEVELOPMENT, World.PROFESSIONAL, RecordKind.ASSESSMENT, consent)
    assert not policy.can_disclose(World.DEVELOPMENT, World.PROFESSIONAL, RecordKind.MEMORY, consent)


def test_revoked_consent_denies():
    consent = ConsentGrant("c", "u", World.DEVELOPMENT, World.PROFESSIONAL, (RecordKind.ASSESSMENT,), "application", revoked=True)
    assert not PrivacyPolicy().can_disclose(World.DEVELOPMENT, World.PROFESSIONAL, RecordKind.ASSESSMENT, consent)
