from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Iterable, Mapping


class MasteryLevel(str, Enum):
    E0_ENCOUNTERED = 'E0_ENCOUNTERED'
    E1_REPRESENTED = 'E1_REPRESENTED'
    E2_PROCEDURAL = 'E2_PROCEDURAL'
    E3_APPLIED = 'E3_APPLIED'
    E4_TRANSFER = 'E4_TRANSFER'
    E5_VERIFIED_MASTERY = 'E5_VERIFIED_MASTERY'


MASTERY_ORDER = {
    MasteryLevel.E0_ENCOUNTERED: 0,
    MasteryLevel.E1_REPRESENTED: 1,
    MasteryLevel.E2_PROCEDURAL: 2,
    MasteryLevel.E3_APPLIED: 3,
    MasteryLevel.E4_TRANSFER: 4,
    MasteryLevel.E5_VERIFIED_MASTERY: 5,
}


class MasteryError(ValueError):
    pass


@dataclass(frozen=True)
class EducationalSystem:
    id: str
    name: str
    jurisdiction: str
    description: str = ''
    source_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class InstitutionType:
    id: str
    name: str
    level_ids: frozenset[str] = frozenset()


@dataclass(frozen=True)
class EducationLevel:
    id: str
    name: str
    sequence: int
    parent_id: str | None = None


@dataclass(frozen=True)
class Discipline:
    id: str
    name: str
    parent_id: str | None = None


@dataclass(frozen=True)
class Domain:
    id: str
    name: str
    discipline_id: str
    parent_id: str | None = None


@dataclass(frozen=True)
class Concept:
    id: str
    name: str
    domain_id: str
    description: str = ''


@dataclass(frozen=True)
class Prerequisite:
    concept_id: str
    prerequisite_concept_id: str
    strength: str = 'required'


@dataclass(frozen=True)
class LearningObjective:
    id: str
    concept_id: str
    statement: str
    cognitive_level: str | None = None


@dataclass(frozen=True)
class Pedagogy:
    id: str
    name: str
    principles: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class Curriculum:
    id: str
    system_id: str
    level_id: str
    name: str
    concept_ids: tuple[str, ...] = ()
    objective_ids: tuple[str, ...] = ()
    pedagogy_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Assessment:
    id: str
    objective_id: str
    method: str
    criterion: str
    benchmark_id: str | None = None


@dataclass(frozen=True)
class Skill:
    id: str
    name: str
    description: str = ''


@dataclass(frozen=True)
class Competency:
    id: str
    name: str
    skill_ids: frozenset[str] = frozenset()
    concept_ids: frozenset[str] = frozenset()


@dataclass(frozen=True)
class LearningPath:
    id: str
    name: str
    ordered_objective_ids: tuple[str, ...]
    rationale: str = ''


@dataclass(frozen=True)
class TeachingStrategy:
    id: str
    name: str
    pedagogy_id: str
    target_mastery: MasteryLevel
    adaptations: tuple[str, ...] = ()


@dataclass(frozen=True)
class Misconception:
    id: str
    concept_id: str
    description: str
    diagnostic_signals: tuple[str, ...] = ()
    correction_strategies: tuple[str, ...] = ()


@dataclass(frozen=True)
class EducationalEvidence:
    id: str
    evidence_type: str
    target_id: str
    artifact_hash: str
    test_hash: str
    independently_verified: bool = False
    result: str = ''


@dataclass(frozen=True)
class EducationalBenchmark:
    id: str
    name: str
    version: str
    objective_ids: tuple[str, ...] = ()
    conditions_hash: str = ''
    result_hash: str = ''
    reproduced: bool = False
    independently_verified: bool = False


@dataclass(frozen=True)
class EducationalQualification:
    target_id: str
    mastery: MasteryLevel
    evidence_ids: tuple[str, ...]
    benchmark_ids: tuple[str, ...]
    independently_verified: bool
    status: str


@dataclass(frozen=True)
class MasteryProfile:
    breadth: float | None = None
    depth: float | None = None
    reasoning: float | None = None
    problem_solving: float | None = None
    research: float | None = None
    retrieval: float | None = None
    tool_use: float | None = None
    engineering: float | None = None
    cross_domain_transfer: float | None = None
    learning: float | None = None
    self_critique: float | None = None
    verification: float | None = None
    reproducibility: float | None = None

    def as_dict(self) -> Mapping[str, float | None]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class MasteryRecord:
    target_id: str
    level: MasteryLevel = MasteryLevel.E0_ENCOUNTERED
    evidence_ids: tuple[str, ...] = ()
    benchmark_ids: tuple[str, ...] = ()
    independent_verification: bool = False

    def observe(
        self,
        level: MasteryLevel,
        *,
        evidence_ids: Iterable[str] = (),
        benchmark_ids: Iterable[str] = (),
        independently_verified: bool = False,
    ) -> 'MasteryRecord':
        if MASTERY_ORDER[level] < MASTERY_ORDER[self.level]:
            raise MasteryError(
                f'mastery cannot regress implicitly: {self.level.value} -> {level.value}'
            )
        evidence = (*self.evidence_ids, *tuple(evidence_ids))
        benchmarks = (*self.benchmark_ids, *tuple(benchmark_ids))
        verified = self.independent_verification or independently_verified
        if level is MasteryLevel.E5_VERIFIED_MASTERY:
            if not evidence:
                raise MasteryError('verified mastery requires evidence')
            if not benchmarks:
                raise MasteryError('verified mastery requires benchmark evidence')
            if not verified:
                raise MasteryError('verified mastery requires independent verification')
        return replace(
            self,
            level=level,
            evidence_ids=evidence,
            benchmark_ids=benchmarks,
            independent_verification=verified,
        )


@dataclass
class EducationalGraph:
    systems: dict[str, EducationalSystem] = field(default_factory=dict)
    institution_types: dict[str, InstitutionType] = field(default_factory=dict)
    levels: dict[str, EducationLevel] = field(default_factory=dict)
    disciplines: dict[str, Discipline] = field(default_factory=dict)
    domains: dict[str, Domain] = field(default_factory=dict)
    concepts: dict[str, Concept] = field(default_factory=dict)
    prerequisites: tuple[Prerequisite, ...] = ()
    objectives: dict[str, LearningObjective] = field(default_factory=dict)
    pedagogies: dict[str, Pedagogy] = field(default_factory=dict)
    curricula: dict[str, Curriculum] = field(default_factory=dict)
    assessments: dict[str, Assessment] = field(default_factory=dict)
    skills: dict[str, Skill] = field(default_factory=dict)
    competencies: dict[str, Competency] = field(default_factory=dict)
    paths: dict[str, LearningPath] = field(default_factory=dict)
    strategies: dict[str, TeachingStrategy] = field(default_factory=dict)
    misconceptions: dict[str, Misconception] = field(default_factory=dict)
    evidence: dict[str, EducationalEvidence] = field(default_factory=dict)
    benchmarks: dict[str, EducationalBenchmark] = field(default_factory=dict)
    mastery: dict[str, MasteryRecord] = field(default_factory=dict)

    def add_system(self, value: EducationalSystem) -> None:
        self._put(self.systems, value.id, value)

    def add_institution_type(self, value: InstitutionType) -> None:
        self._put(self.institution_types, value.id, value)

    def add_level(self, value: EducationLevel) -> None:
        self._put(self.levels, value.id, value)

    def add_discipline(self, value: Discipline) -> None:
        self._put(self.disciplines, value.id, value)

    def add_domain(self, value: Domain) -> None:
        self._put(self.domains, value.id, value)

    def add_concept(self, value: Concept) -> None:
        self._put(self.concepts, value.id, value)

    def add_objective(self, value: LearningObjective) -> None:
        self._put(self.objectives, value.id, value)

    def add_pedagogy(self, value: Pedagogy) -> None:
        self._put(self.pedagogies, value.id, value)

    def add_curriculum(self, value: Curriculum) -> None:
        self._put(self.curricula, value.id, value)

    def add_assessment(self, value: Assessment) -> None:
        self._put(self.assessments, value.id, value)

    def add_skill(self, value: Skill) -> None:
        self._put(self.skills, value.id, value)

    def add_competency(self, value: Competency) -> None:
        self._put(self.competencies, value.id, value)

    def add_learning_path(self, value: LearningPath) -> None:
        self._put(self.paths, value.id, value)

    def add_strategy(self, value: TeachingStrategy) -> None:
        self._put(self.strategies, value.id, value)

    def add_misconception(self, value: Misconception) -> None:
        self._put(self.misconceptions, value.id, value)

    def add_evidence(self, value: EducationalEvidence) -> None:
        self._put(self.evidence, value.id, value)

    def add_benchmark(self, value: EducationalBenchmark) -> None:
        self._put(self.benchmarks, value.id, value)

    def add_prerequisite(self, value: Prerequisite) -> None:
        if value not in self.prerequisites:
            self.prerequisites = (*self.prerequisites, value)

    def record_mastery(self, record: MasteryRecord) -> None:
        self.mastery[record.target_id] = record

    def prerequisites_for(self, concept_id: str) -> tuple[str, ...]:
        return tuple(
            edge.prerequisite_concept_id
            for edge in self.prerequisites
            if edge.concept_id == concept_id
        )

    def learning_sequence(self, objective_ids: Iterable[str]) -> tuple[LearningObjective, ...]:
        return tuple(self.objectives[item] for item in objective_ids)

    @staticmethod
    def _put(store: dict[str, object], key: str, value: object) -> None:
        if key in store:
            raise ValueError(f'educational object already registered: {key}')
        store[key] = value


def qualify_mastery(
    record: MasteryRecord,
    *,
    evidence: Iterable[EducationalEvidence],
    benchmarks: Iterable[EducationalBenchmark],
) -> EducationalQualification:
    evidence = tuple(evidence)
    benchmarks = tuple(benchmarks)
    if not evidence:
        raise MasteryError('qualification requires evidence')
    if not benchmarks:
        raise MasteryError('qualification requires benchmark evidence')
    if not any(item.independently_verified for item in evidence):
        raise MasteryError('qualification requires independently verified evidence')
    if not any(item.reproduced and item.independently_verified for item in benchmarks):
        raise MasteryError(
            'qualification requires reproduced and independently verified benchmark evidence'
        )
    if record.level is not MasteryLevel.E5_VERIFIED_MASTERY:
        raise MasteryError('qualification requires E5 verified mastery')
    return EducationalQualification(
        target_id=record.target_id,
        mastery=record.level,
        evidence_ids=tuple(item.id for item in evidence),
        benchmark_ids=tuple(item.id for item in benchmarks),
        independently_verified=True,
        status='QUALIFIED',
    )
