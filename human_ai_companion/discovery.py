from dataclasses import dataclass, field


@dataclass(frozen=True)
class DiscoveryObservation:
    experiment_id: str
    capability_id: str
    interest: float | None = None
    performance: float | None = None
    persistence: float | None = None
    learning: float | None = None
    user_feedback: float | None = None
    real_world_experience: float | None = None


@dataclass
class DiscoveryEngine:
    observations: list[DiscoveryObservation] = field(default_factory=list)

    def observe(self, observation: DiscoveryObservation) -> None:
        self.observations.append(observation)

    def hypotheses(self) -> dict[str, dict[str, float]]:
        grouped: dict[str, list[DiscoveryObservation]] = {}
        for item in self.observations:
            grouped.setdefault(item.capability_id, []).append(item)
        result: dict[str, dict[str, float]] = {}
        for capability, rows in grouped.items():
            values = {}
            for name in ("interest", "performance", "persistence", "learning", "user_feedback", "real_world_experience"):
                samples = [getattr(row, name) for row in rows if getattr(row, name) is not None]
                if samples:
                    values[name] = sum(samples) / len(samples)
            result[capability] = values
        return result
