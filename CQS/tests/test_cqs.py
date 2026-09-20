from dataclasses import asdict
from cqs import CQSService, Capability, EvidenceRecord, QualificationState
from cqs.hashing import content_hash
from cqs.models import EvidenceStatus


def capability():
    return Capability(
        capability_id="math.wiedemann.v1",
        version="1.0.0",
        schema_version="cqs-0.1",
        domain="mathematics",
        name="Wiedemann sparse linear algebra",
        description="Compute sequence-based information about sparse matrices.",
        inputs=("sparse_matrix",),
        outputs=("minimal_polynomial",),
        mechanism={"description": "Krylov sequence + Berlekamp-Massey"},
        implementation={"repository": "example", "commit": "immutable"},
        qualification_profile="mathematical.v1",
    )


def evidence(cid, version, kind, status=EvidenceStatus.PRESENT, n=1):
    raw = {
        "evidence_id": f"E-{kind}-{n}",
        "capability_id": cid,
        "capability_version": version,
        "evidence_type": kind,
        "status": status,
        "producer": "test",
        "provenance": {"test": "unit"},
        "metrics": {},
        "observations": {},
    }
    return EvidenceRecord(**raw, content_hash=content_hash(raw))


def test_not_measured_is_not_failed():
    s = CQSService()
    c = s.register_capability(capability())
    s.append_evidence(evidence(c.capability_id, c.version, "SPECIFICATION"))
    d = s.qualify(c.capability_id, c.version)
    assert d.state != QualificationState.QUALIFIED
    assert any("IMPLEMENTATION" in x for x in d.unmet_requirements)


def test_qualification_requires_all_profile_evidence():
    s = CQSService()
    c = s.register_capability(capability())
    kinds = ["SPECIFICATION","IMPLEMENTATION","RUNTIME","PERFORMANCE",
             "REPRODUCTION","INDEPENDENCE","VERIFICATION","FORMAL_CORRECTNESS"]
    for i, kind in enumerate(kinds):
        s.append_evidence(evidence(c.capability_id, c.version, kind, n=i))
    d = s.qualify(c.capability_id, c.version)
    assert d.state == QualificationState.QUALIFIED
    assert s.availability(c.capability_id, c.version) is True
    assert s.ledger.verify() is True


def test_security_missing_does_not_become_qualified():
    s = CQSService()
    c = s.register_capability(Capability(**{**asdict(capability()), "qualification_profile":"security.v1"}))
    kinds = ["SPECIFICATION","IMPLEMENTATION","RUNTIME","PERFORMANCE",
             "REPRODUCTION","INDEPENDENCE","VERIFICATION"]
    for i, kind in enumerate(kinds):
        s.append_evidence(evidence(c.capability_id, c.version, kind, n=i))
    d = s.qualify(c.capability_id, c.version)
    assert d.state != QualificationState.QUALIFIED
    assert any("SECURITY" in x for x in d.unmet_requirements)
