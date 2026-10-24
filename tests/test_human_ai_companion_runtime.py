import unittest
from human_ai_companion.runtime import CompanionRuntime
from human_ai_companion.models import EvidenceState, HumanDecision, RecordKind, World, Provenance
from human_ai_companion.life_log import LifeEntry
from human_ai_companion.learning import AssessmentResult, LearningObjective


class CompanionRuntimeTests(unittest.TestCase):
    def test_personal_entry_is_private_and_separate(self):
        r = CompanionRuntime('person-1')
        entry = LifeEntry('life-1', 'person-1', '2026-09-11T00:00:00+00:00', 'private reflection')
        r.add_life_entry(entry)
        self.assertEqual(len(r.life_log.timeline()), 1)
        self.assertEqual(r.companion.records(World.PROFESSIONAL), ())

    def test_learning_assessment_enters_development_world(self):
        r = CompanionRuntime('person-1')
        r.add_learning_objective(LearningObjective('obj-1', 'Python', 'python'))
        r.assess(AssessmentResult('assess-1', 'python', 0.9, True, 'raw-1'))
        records = r.companion.records(World.DEVELOPMENT)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].evidence_state, EvidenceState.ASSESSED)

    def test_human_is_required_for_consequential_action(self):
        r = CompanionRuntime('person-1')
        with self.assertRaises(PermissionError):
            r.authorize(HumanDecision('d-1', 'person-1', 'apply', True, 'AI'))
        r.authorize(HumanDecision('d-2', 'person-1', 'apply', True, 'HUMAN'))

    def test_subject_isolation(self):
        r = CompanionRuntime('person-1')
        p = Provenance('s', 'r', '0' * 64, '2026-09-11T00:00:00+00:00', 'HUMAN')
        from human_ai_companion.models import Record
        with self.assertRaises(PermissionError):
            r.companion.record(Record('x', 'person-2', World.DEVELOPMENT, RecordKind.ATTEMPT, {}, EvidenceState.REPORTED, p))


if __name__ == '__main__':
    unittest.main()
