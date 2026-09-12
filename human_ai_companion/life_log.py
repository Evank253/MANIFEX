from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class LifeEntry:
    entry_id: str
    subject_id: str
    occurred_at: datetime
    content: str
    tags: tuple[str, ...] = ()
    private: bool = True


@dataclass
class LifeLog:
    subject_id: str
    entries: list[LifeEntry] = field(default_factory=list)

    def add(self, entry: LifeEntry) -> None:
        if entry.subject_id != self.subject_id:
            raise PermissionError("life entry subject mismatch")
        if not entry.private:
            raise ValueError("Life Log entries must be private by default")
        self.entries.append(entry)

    def timeline(self) -> tuple[LifeEntry, ...]:
        return tuple(sorted(self.entries, key=lambda item: item.occurred_at))

    def professional_evidence(self) -> tuple[LifeEntry, ...]:
        return ()
