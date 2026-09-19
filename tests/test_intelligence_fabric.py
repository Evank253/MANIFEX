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
    raise AssertionError(f'expected {expected.__name__}')


def make_capability(capability_id: str = 'cap-1') -> CapabilityGenome:
    return CapabilityGenome(
        id=capability_id,
        name='Numerical Optimization',
        category='optimization',
        function='optimize a numeric objective',
        mechanism='iterative search',
        provenance=Provenance(
            source='public-research',
            repository='example/repository',
            commit='immutable-commit',
            tree_hash='tree-hash',
            license='MIT',
        ),
    )


def add_verified_evidence(cap: CapabilityGenome) -> CapabilityGenome:
    cap = cap.with_evidence(EvidenceReference(
        evidence_id='ev-1',
        evidence_type='reproduction',
        artifact_hash='artifact-hash',
        test_hash='test-hash',
        independently_verified=True,
    ))
    return cap.with_benchmark(BenchmarkResult(
        benchmark_id='bench-1',
        benchmark_version='1',
        metric='accuracy',
        value=0.99,
        conditions_hash='conditions',
        raw_result_hash='raw-result',
        reproduced=True,
        independently_verified=True,
    ))


def qualify(cap: CapabilityGenome) -> CapabilityGenome:
    for state in (
        QualificationState.EXTRACTED,
        QualificationState.REPRODUCED,
        QualificationState.BENCHMARKED,
        QualificationState.SECURITY_TESTED,
        QualificationState.VERIFIED,
    ):
        cap = cap.transition(state)
    return cap


def test_capability_requires_sequential_qualification():
    cap = make_capability()
    with raises(QualificationError):
        cap.transition(QualificationState.QUALIFIED)


def test_discovered_to_qualified_cannot_skip():
    cap = make_capability()
    with raises(QualificationError):
        cap.transition(QualificationState.QUALIFIED)


def test_capability_can_follow_complete_qualification_chain():
    cap = add_verified_evidence(qualify(make_capability()))
    cap = cap.transition(QualificationState.QUALIFIED)
    assert cap.qualified
    assert cap.can_execute()


def test_known_vulnerability_blocks_qualification():
    cap = make_capability()
    cap = CapabilityGenome(**{**cap.__dict__, 'known_vulnerabilities': ('known vulnerability',)})
    cap = add_verified_evidence(qualify(cap))
    with raises(QualificationError):
        cap.transition(QualificationState.QUALIFIED)


def test_registry_only_returns_qualified_capabilities():
    registry = CapabilityRegistry()
    unqualified = make_capability()
    qualified = add_verified_evidence(qualify(make_capability('cap-2')))
    qualified = qualified.transition(QualificationState.QUALIFIED)
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
    assert values['breadth'] == 0.8
    assert values['reasoning'] == 0.9
    assert values['verification'] == 1.0


def test_capability_records_are_immutable():
    cap = make_capability()
    with raises(Exception):
        cap.name = 'tampered'


if __name__ == '__main__':
    tests = [v for k, v in globals().items() if k.startswith('test_')]
    for test in tests:
        test()
    print(f'PASS {len(tests)} intelligence fabric tests')
