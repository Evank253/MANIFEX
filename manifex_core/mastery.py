from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .education import (
    Assessment,
    EducationalGraph,
    MasteryLevel,
    MasteryRecord,
    MASTERY_ORDER,
)


class MasteryDimension(str, Enum):
    KNOWLEDGE = 'knowledge'
    UNDERSTANDING = 'understanding'
    PROCEDURAL = 'procedural'
    APPLICATION = 'application'
    TRANSFER = 'transfer'
    RESEARCH = 'research'
    TEACHING = 'teaching'
    CRITIQUE = 'critique'
    VERIFICATION = 'verification'
    REPRODUCIBILITY = 'reproducibility'


@dataclass(frozen=True)
class MasteryObservation:
    target_id: str
    dimension: MasteryDimension
    score: float
    evidence_id: str
    benchmark_id: str | None = None
    independent_verification: bool = False
    context: str = ''

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError('mastery observation score must be between 0 and 1')
        if not self.evidence_id:
            raise ValueError('mastery observation requires evidence')


@dataclass(frozen=True)
class MasteryAssessment:
    target_id: str
    observations: tuple[MasteryObservation, ...]
    current_level: MasteryLevel
    next_level: MasteryLevel | None
    gaps: tuple[str, ...]
    missing_prerequisites: tuple[str, ...]
    recommended_assessments: tuple[Assessment, ...]
    evidence_ids: tuple[str, ...]
    benchmark_ids: tuple[str, ...]
    evidence_grounded: bool


class EducationalMasteryEngine:
    """Evidence-grounded mastery assessment; it never infers mastery from self-report."""

    DIMENSION_LEVELS = {
        MasteryDimension.KNOWLEDGE: MasteryLevel.E1_REPRESENTED,
        MasteryDimension.UNDERSTANDING: MasteryLevel.E1_REPRESENTED,
        MasteryDimension.PROCEDURAL: MasteryLevel.E2_PROCEDURAL,
        MasteryDimension.APPLICATION: MasteryLevel.E3_APPLIED,
        MasteryDimension.TRANSFER: MasteryLevel.E4_TRANSFER,
        MasteryDimension.VERIFICATION: MasteryLevel.E5_VERIFIED_MASTERY,
        MasteryDimension.REPRODUCIBILITY: MasteryLevel.E5_VERIFIED_MASTERY,
    }

    def __init__(self, graph: EducationalGraph):
        self.graph = graph

    def assess(
        self,
        target_id: str,
        observations: tuple[MasteryObservation, ...] = (),
    ) -> MasteryAssessment:
        relevant = tuple(item for item in observations if item.target_id == target_id)
        current = self._derive_level(relevant)
        next_level = self._next_level(current)
        gaps = self._gaps(current, relevant)
        missing = self._missing_prerequisites(target_id)
        recommended = self._recommended_assessments(target_id, gaps)
        evidence_ids = tuple(dict.fromkeys(item.evidence_id for item in relevant))
        benchmark_ids = tuple(
            dict.fromkeys(item.benchmark_id for item in relevant if item.benchmark_id)
        )
        return MasteryAssessment(
            target_id=target_id,
            observations=relevant,
            current_level=current,
            next_level=next_level,
            gaps=gaps,
            missing_prerequisites=missing,
            recommended_assessments=recommended,
            evidence_ids=evidence_ids,
            benchmark_ids=benchmark_ids,
            evidence_grounded=bool(relevant),
        )

    def update_record(
        self,
        record: MasteryRecord,
        observations: tuple[MasteryObservation, ...],
    ) -> MasteryRecord:
        assessment = self.assess(record.target_id, observations)
        if not assessment.evidence_grounded:
            return record
        return record.observe(
            assessment.current_level,
            evidence_ids=assessment.evidence_ids,
            benchmark_ids=assessment.benchmark_ids,
            independently_verified=all(
                item.independent_verification for item in assessment.observations
            ),
        )

    def _derive_level(
        self, observations: tuple[MasteryObservation, ...]
    ) -> MasteryLevel:
        if not observations:
            return MasteryLevel.E0_ENCOUNTERED

        level = MasteryLevel.E0_ENCOUNTERED
        for candidate in MasteryLevel:
            required = [
                item for item in observations
                if self.DIMENSION_LEVELS.get(item.dimension) is candidate
            ]
            if required and all(item.score >= 0.8 for item in required):
                if MASTERY_ORDER[candidate] > MASTERY_ORDER[level]:
                    level = candidate

        if level is MasteryLevel.E4_TRANSFER:
            verified = [
                item for item in observations
                if item.dimension in (
                    MasteryDimension.VERIFICATION,
                    MasteryDimension.REPRODUCIBILITY,
                )
            ]
            if not any(
                item.score >= 0.8 and item.independent_verification
                for item in verified
            ):
                return MasteryLevel.E4_TRANSFER

        return level

    @staticmethod
    def _next_level(level: MasteryLevel) -> MasteryLevel | None:
        order = MASTERY_ORDER[level]
        for candidate in MasteryLevel:
            if MASTERY_ORDER[candidate] == order + 1:
                return candidate
        return None

    def _gaps(
        self,
        current: MasteryLevel,
        observations: tuple[MasteryObservation, ...],
    ) -> tuple[str, ...]:
        observed = {item.dimension for item in observations if item.score >= 0.8}
        gaps = []
        if MASTERY_ORDER[current] >= 1 and MasteryDimension.KNOWLEDGE not in observed:
            gaps.append('knowledge')
        if MASTERY_ORDER[current] >= 2 and MasteryDimension.PROCEDURAL not in observed:
            gaps.append('procedural')
        if MASTERY_ORDER[current] >= 3 and MasteryDimension.APPLICATION not in observed:
            gaps.append('application')
        if MASTERY_ORDER[current] >= 4 and MasteryDimension.TRANSFER not in observed:
            gaps.append('transfer')
        return tuple(gaps)

    def _missing_prerequisites(self, target_id: str) -> tuple[str, ...]:
        if target_id not in self.graph.concepts:
            return ()
        prereqs = self.graph.prerequisites_for(target_id)
        missing = []
        for prerequisite in prereqs:
            record = self.graph.mastery.get(prerequisite)
            if record is None or MASTERY_ORDER[record.level] < MASTERY_ORDER[MasteryLevel.E3_APPLIED]:
                missing.append(prerequisite)
        return tuple(missing)

    def _recommended_assessments(
        self, target_id: str, gaps: tuple[str, ...]
    ) -> tuple[Assessment, ...]:
        objectives = {
            item.id: item
            for item in self.graph.objectives.values()
            if item.concept_id == target_id
        }
        return tuple(
            assessment
            for assessment in self.graph.assessments.values()
            if assessment.objective_id in objectives
            and (not gaps or assessment.method in gaps or assessment.criterion in gaps)
        )
