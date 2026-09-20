from contextlib import contextmanager

from manifex_core.education import (
    Assessment,
    Concept,
    EducationalGraph,
    LearningObjective,
    MasteryLevel,
    MasteryRecord,
    Prerequisite,
)
from manifex_core.mastery import (
    EducationalMasteryEngine,
    MasteryDimension,
    MasteryObservation,
)


@contextmanager
def raises(expected):
    try:
        yield
    except expected:
        return
    raise AssertionError(f'expected {expected.__name__}')


def test_no_evidence_means_not_measured():
    engine = EducationalMasteryEngine(EducationalGraph())
    result = engine.assess('sorting')
    assert result.current_level is MasteryLevel.E0_ENCOUNTERED
    assert result.evidence_grounded is False


def test_application_requires_application_evidence():
    engine = EducationalMasteryEngine(EducationalGraph())
    observations = (
        MasteryObservation('sorting', MasteryDimension.KNOWLEDGE, 0.95, 'ev-k'),
        MasteryObservation('sorting', MasteryDimension.PROCEDURAL, 0.95, 'ev-p'),
    )
    result = engine.assess('sorting', observations)
    assert result.current_level is MasteryLevel.E2_PROCEDURAL
    assert result.next_level is MasteryLevel.E3_APPLIED


def test_transfer_requires_transfer_evidence():
    engine = EducationalMasteryEngine(EducationalGraph())
    observations = (
        MasteryObservation('sorting', MasteryDimension.KNOWLEDGE, 0.95, 'ev-k'),
        MasteryObservation('sorting', MasteryDimension.PROCEDURAL, 0.95, 'ev-p'),
        MasteryObservation('sorting', MasteryDimension.APPLICATION, 0.95, 'ev-a'),
    )
    result = engine.assess('sorting', observations)
    assert result.current_level is MasteryLevel.E3_APPLIED


def test_missing_prerequisite_is_reported():
    graph = EducationalGraph()
    graph.add_concept(Concept('sorting', 'Sorting', 'algorithms'))
    graph.add_prerequisite(Prerequisite('sorting', 'complexity'))
    engine = EducationalMasteryEngine(graph)
    result = engine.assess('sorting')
    assert result.missing_prerequisites == ('complexity',)


def test_record_update_uses_observed_evidence_only():
    graph = EducationalGraph()
    engine = EducationalMasteryEngine(graph)
    record = MasteryRecord('sorting')
    observations = (
        MasteryObservation('sorting', MasteryDimension.KNOWLEDGE, 0.95, 'ev-k'),
        MasteryObservation('sorting', MasteryDimension.PROCEDURAL, 0.95, 'ev-p'),
        MasteryObservation('sorting', MasteryDimension.APPLICATION, 0.95, 'ev-a'),
    )
    updated = engine.update_record(record, observations)
    assert updated.level is MasteryLevel.E3_APPLIED
    assert updated.evidence_ids == ('ev-k', 'ev-p', 'ev-a')


def test_assessment_can_recommend_matching_assessment():
    graph = EducationalGraph()
    graph.add_objective(LearningObjective('obj', 'sorting', 'Apply sorting'))
    graph.add_assessment(Assessment('a', 'obj', 'application', 'application'))
    engine = EducationalMasteryEngine(graph)
    result = engine.assess(
        'sorting',
        (MasteryObservation('sorting', MasteryDimension.KNOWLEDGE, 0.95, 'ev-k'),),
    )
    assert result.recommended_assessments[0].id == 'a'


if __name__ == '__main__':
    tests = [v for k, v in globals().items() if k.startswith('test_')]
    for test in tests:
        test()
    print(f'PASS {len(tests)} educational mastery tests')
