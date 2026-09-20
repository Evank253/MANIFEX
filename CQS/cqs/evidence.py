"""Append-only in-memory evidence store for CQS v0.1."""

from __future__ import annotations
from dataclasses import asdict
from .models import EvidenceRecord
from .hashing import content_hash


class EvidenceStore:
    def __init__(self) -> None:
        self._records: dict[str, EvidenceRecord] = {}

    def append(self, record: EvidenceRecord) -> EvidenceRecord:
        if record.evidence_id in self._records:
            raise ValueError("evidence_id already exists; historical evidence is immutable")
        expected = content_hash({k: v for k, v in asdict(record).items() if k != "content_hash"})
        if record.content_hash != expected:
            raise ValueError("evidence content hash does not match canonical record")
        self._records[record.evidence_id] = record
        return record

    def get(self, evidence_id: str) -> EvidenceRecord:
        return self._records[evidence_id]

    def for_capability(self, capability_id: str, version: str) -> list[EvidenceRecord]:
        return [
            r for r in self._records.values()
            if r.capability_id == capability_id and r.capability_version == version
        ]
