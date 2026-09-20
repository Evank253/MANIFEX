"""Hash-chained qualification decision ledger."""

from __future__ import annotations
from dataclasses import asdict, dataclass
from .hashing import content_hash
from .models import QualificationDecision


@dataclass(frozen=True)
class LedgerEntry:
    sequence: int
    previous_hash: str
    decision: QualificationDecision
    entry_hash: str


class QualificationLedger:
    def __init__(self) -> None:
        self._entries: list[LedgerEntry] = []

    def append(self, decision: QualificationDecision) -> LedgerEntry:
        previous = self._entries[-1].entry_hash if self._entries else "GENESIS"
        payload = {
            "sequence": len(self._entries),
            "previous_hash": previous,
            "decision": asdict(decision),
        }
        entry = LedgerEntry(
            sequence=len(self._entries),
            previous_hash=previous,
            decision=decision,
            entry_hash=content_hash(payload),
        )
        self._entries.append(entry)
        return entry

    def verify(self) -> bool:
        previous = "GENESIS"
        for i, entry in enumerate(self._entries):
            if entry.sequence != i or entry.previous_hash != previous:
                return False
            payload = {
                "sequence": entry.sequence,
                "previous_hash": entry.previous_hash,
                "decision": asdict(entry.decision),
            }
            if entry.entry_hash != content_hash(payload):
                return False
            previous = entry.entry_hash
        return True

    @property
    def entries(self) -> tuple[LedgerEntry, ...]:
        return tuple(self._entries)
