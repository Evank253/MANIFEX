from __future__ import annotations

from contextlib import contextmanager

from manifex_core.education import (
    Concept,
    Discipline,
    Domain,
    EducationalBenchmark,
    EducationalEvidence,
    EducationalGraph,
    EducationalSystem,
    EducationLevel,
    LearningObjective,
    MasteryError,
    MasteryLevel,
    MasteryProfile,
    MasteryRecord,
    Prerequisite,
    qualify_mastery,
)


@contextmanager
def raises(expected: type[BaseException]):
    try:
        yield
    except expected:
        return
    raise AssertionError(f'expected {expected.__name__}')


def test_educational_genome_can_represent_hierarchy():
    graph = EducationalGraph()
    graph.add_system(EducationalSystem('sys-us', 'Example K-12', 'US'))
    graph.add_level(EducationLevel('level-secondary', 'Secondary', 2))
    graph.add_discipline(Discipline('cs', 'Computer Science'))
    graph.add_domain(Domain('algorithms', 'Algorithms', 'cs'))
    graph.add_concept(Concept('sorting', 'Sorting', 'algorithms'))
    graph.add_objective(LearningObjective('obj-sorting', 'sorting', 'Explain and implement sorting'))
    graph.add_prerequisite(Prerequisite('sorting', 'complexity'))

    assert graph.concepts['sorting'].domain_id == 'algorithms'
    assert graph.prerequisites_for('sorting') == ('complexity',)


def test_mastery_levels_are_ordered_and_multidimensional():
    record = MasteryRecord('sorting')
    record = record.observe(MasteryLevel.E1_REPRESENTED)
    record = record.observe(MasteryLevel.E2_PROCEDURAL)
    record = record.observe(MasteryLevel.E3_APPLIED)
    record = record.observe(MasteryLevel.E4_TRANSFER)
    assert record.level is MasteryLevel.E4_TRANSFER
    profile = MasteryProfile(breadth=0.8, reasoning=0.9, verification=1.0)
    assert profile.as_dict()['reasoning'] == 0.9


def test_verified_mastery_requires_evidence_and_independent_verification():
    record = MasteryRecord('sorting')
    with raises(MasteryError):
        record.observe(MasteryLevel.E5_VERIFIED_MASTERY)


def test_verified_mastery_accepts_complete_evidence():
    record = MasteryRecord('sorting').observe(
        MasteryLevel.E5_VERIFIED_MASTERY,
        evidence_ids=('ev-1',),
        benchmark_ids=('bench-1',),
        independently_verified=True,
    )
    evidence = (
        EducationalEvidence('ev-1', 'reproduction', 'sorting', 'artifact', 'test', True, 'PASS'),
    )
    benchmarks = (
        EducationalBenchmark('bench-1', 'sorting benchmark', '1', ('obj-sorting',), 'conditions', 'result', True, True),
    )
    qualification = qualify_mastery(record, evidence=evidence, benchmarks=benchmarks)
    assert qualification.status == 'QUALIFIED'
    assert qualification.mastery is MasteryLevel.E5_VERIFIED_MASTERY


def test_mastery_cannot_be_reduced_implicitly():
    record = MasteryRecord('sorting').observe(MasteryLevel.E3_APPLIED)
    with raises(MasteryError):
        record.observe(MasteryLevel.E1_REPRESENTED)


def test_graph_rejects_duplicate_objects():
    graph = EducationalGraph()
    graph.add_concept(Concept('c1', 'Concept', 'd1'))
    with raises(ValueError):
        graph.add_concept(Concept('c1', 'Concept', 'd1'))


if __name__ == '__main__':
    tests = [v for k, v in globals().items() if k.startswith('test_')]
    for test in tests:
        test()
    print(f'PASS {len(tests)} educational intelligence tests')
