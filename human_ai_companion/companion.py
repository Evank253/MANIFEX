from dataclasses import dataclass
from .constitution import CONSTITUTION
from .models import HumanDecision, Record, World
from .privacy import PrivacyPolicy


@dataclass
class HumanAICompanion:
    subject_id: str
    constitution: object = CONSTITUTION
    privacy: PrivacyPolicy = PrivacyPolicy()

    def __post_init__(self) -> None:
        self.constitution.validate()
        self._records: dict[str, Record] = {}

    def record(self, record: Record) -> None:
        if record.subject_id != self.subject_id:
            raise PermissionError("record subject does not match companion owner")
        self._records[record.record_id] = record

    def records(self, world: World | None = None) -> tuple[Record, ...]:
        values = self._records.values()
        if world is not None:
            values = (record for record in values if record.world == world)
        return tuple(values)

    def authorize_consequential_action(self, decision: HumanDecision) -> None:
        if decision.subject_id != self.subject_id:
            raise PermissionError("decision subject does not match companion owner")
        if not decision.authorized or decision.decided_by != "HUMAN":
            raise PermissionError("consequential action requires explicit human authorization")
