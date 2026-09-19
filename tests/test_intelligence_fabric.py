from __future__ import annotations

from contextlib import contextmanager

from manifex_core.intelligence import (
    BenchmarkResult,
    CapabilityGenome,
    CapabilityRegistry,
    EvidenceReference,
    IntelligenceProfile,
    Provenance,
    QualificationError,
    QualificationState,
    build_evidence_package,
)


@contextmanager
def raises(expected: type[BaseException]):
    try:
        yield
    except expected:
        return
    raise AssertionError(f"expected {expected.__name__}")


def make_capability() -> CapabilityGenome:
    return CapabilityGenome(
        id="cap-1",
        name="Numerical Optimization",
        category="optimization",
        function="optimize a numeric objective",
        mechanism="iterative search",
        provenance=Provenance(
            source="public-research",
            repository="example/repository",
            commit="immutable-commit",
            tree_hash="tree-hash",
            license="MIT",
        ),
    )


def add_verified_evidence(cap: CapabilityGenome) -> None:
    cap.add_evidence(EvidenceReference(
        evidence_id="ev-1",
        evidence_type="reproduction",
        artifact_hash="artifact-hash",
        test_hash="test-hash",
        independently_verified=True,
    ))
    cap.add_benchmark(BenchmarkResult(
        benchmark_id="bench-1",
        benchmark_version="1",
        metric="accuracy",
        value=0.99,
        conditions_hash="conditions",
        raw_result_hash="raw-result",
        reproduced=True,
        independently_verified=True,
    ))


def test_capability_requires_sequential_qualification():
    cap = make_capability()
    with raises(QualificationError):
        cap.transition(QualificationState.QUALIFIED)


def test_discovered_to_qualified_cannot_skip():
    cap = make_capability()
    with raises(QualificationError):
        cap.transition(QualificationState.QUALIFIED)


def test_capability_can_follow_complete_qualification_chain():
    cap = make_capability()
    for state in (
        QualificationState.EXTRACTED,
        QualificationState.REPRODUCED,
        QualificationState.BENCHMARKED,
        QualificationState.SECURITY_TESTED,
        QualificationState.VERIFIED,
    ):
        cap.transition(state)
    add_verified_evidence(cap)
    cap.transition(QualificationState.QUALIFIED)
    assert cap.qualified
    assert cap.can_execute()


def test_known_vulnerability_blocks_qualification():
    cap = make_capability()
    cap.known_vulnerabilities = ("known vulnerability",)
    add_verified_evidence(cap)
    for state in (
        QualificationState.EXTRACTED,
        QualificationState.REPRODUCED,
        QualificationState.BENCHMARKED,
        QualificationState.SECURITY_TESTED,
        QualificationState.VERIFIED,
    ):
        cap.transition(state)
    with raises(QualificationError):
        cap.transition(QualificationState.QUALIFIED)


def test_registry_only_returns_qualified_capabilities():
    registry = CapabilityRegistry()
    unqualified = make_capability()
    qualified = make_capability()
    qualified.id = "cap-2"
    for state in (
        QualificationState.EXTRACTED,
        QualificationState.REPRODUCED,
        QualificationState.BENCHMARKED,
        QualificationState.SECURITY_TESTED,
        QualificationState.VERIFIED,
    ):
        qualified.transition(state)
    add_verified_evidence(qualified)
    qualified.transition(QualificationState.QUALIFIED)
    registry.register(unqualified)
    registry.register(qualified)
    assert registry.qualified() == (qualified,)


def test_evidence_package_reflects_qualification():
    cap = make_capability()
    package = build_evidence_package(cap)
    assert not package.sufficient_for_qualification
    assert package.qualification is QualificationState.DISCOVERED


def test_intelligence_profile_is_multidimensional():
    profile = IntelligenceProfile(breadth=0.8, reasoning=0.9, verification=1.0)
    values = profile.as_dict()
    assert values["breadth"] == 0.8
    assert values["reasoning"] == 0.9
    assert values["verification"] == 1.0


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    for test in tests:
        test()
    print(f"PASS {len(tests)} intelligence fabric tests")
