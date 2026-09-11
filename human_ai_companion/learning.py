from dataclasses import dataclass, field


@dataclass(frozen=True)
class AssessmentResult:
    assessment_id: str
    capability_id: str
    score: float
    passed: bool
    raw_result_id: str


@dataclass(frozen=True)
class LearningObjective:
    objective_id: str
    capability_id: str
    description: str
    prerequisites: tuple[str, ...] = ()


@dataclass
class LearningEngine:
    objectives: dict[str, LearningObjective] = field(default_factory=dict)
    assessments: list[AssessmentResult] = field(default_factory=list)

    def add_objective(self, objective: LearningObjective) -> None:
        self.objectives[objective.objective_id] = objective

    def record_assessment(self, result: AssessmentResult) -> None:
        if not 0 <= result.score <= 1:
            raise ValueError("assessment score must be between 0 and 1")
        self.assessments.append(result)

    def demonstrated_capabilities(self, threshold: float = 0.8) -> set[str]:
        return {item.capability_id for item in self.assessments if item.passed and item.score >= threshold}

    def next_objectives(self) -> tuple[LearningObjective, ...]:
        demonstrated = self.demonstrated_capabilities()
        return tuple(item for item in self.objectives.values() if item.capability_id not in demonstrated)
