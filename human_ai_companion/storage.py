import json
from pathlib import Path
from typing import Iterable

from .models import Record


class CompanionStore:
    """Append-only JSONL store; callers remain responsible for filesystem policy."""
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: Record) -> None:
        with self.path.open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(self._encode(record), sort_keys=True, separators=(',', ':')) + '\n')

    def read(self) -> tuple[dict, ...]:
        if not self.path.exists():
            return ()
        rows = []
        for line in self.path.read_text(encoding='utf-8').splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return tuple(rows)

    @staticmethod
    def _encode(record: Record) -> dict:
        return {
            'record_id': record.record_id,
            'subject_id': record.subject_id,
            'world': record.world.value,
            'kind': record.kind.value,
            'payload': dict(record.payload),
            'evidence_state': record.evidence_state.value,
            'provenance': {
                'source_id': record.provenance.source_id,
                'source_revision': record.provenance.source_revision,
                'content_sha256': record.provenance.content_sha256,
                'recorded_at': record.provenance.recorded_at,
                'actor': record.provenance.actor,
            },
        }
