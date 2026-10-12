"""Provenance Sync – cryptographic evidence chain."""
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field
import hashlib, json

class HashAlgorithm(str, Enum):
    SHA256 = "sha256"
    SHA3_256 = "sha3_256"
    BLAKE2B = "blake2b"

class ProvenanceRecord(BaseModel):
    record_id: str
    subject_id: str
    subject_type: str
    action: str
    actor_id: str
    parent_ids: List[str] = Field(default_factory=list)
    content_hash: str
    hash_algorithm: HashAlgorithm = HashAlgorithm.SHA256
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    signature: Optional[str] = None

    @staticmethod
    def compute_content_hash(payload, algorithm=HashAlgorithm.SHA256):
        if isinstance(payload, dict):
            data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        elif isinstance(payload, str):
            data = payload.encode()
        else:
            data = payload
        if algorithm == HashAlgorithm.SHA256:
            return hashlib.sha256(data).hexdigest()
        if algorithm == HashAlgorithm.SHA3_256:
            return hashlib.sha3_256(data).hexdigest()
        if algorithm == HashAlgorithm.BLAKE2B:
            return hashlib.blake2b(data).hexdigest()
        raise ValueError(f"Unsupported: {algorithm}")

    @classmethod
    def create(cls, subject_id, subject_type, action, actor_id, content,
               parent_ids=None, metadata=None, algorithm=HashAlgorithm.SHA256, signature=None):
        content_hash = cls.compute_content_hash(content, algorithm)
        record_payload = {
            "subject_id": subject_id, "subject_type": subject_type, "action": action,
            "actor_id": actor_id, "parent_ids": sorted(parent_ids or []),
            "content_hash": content_hash, "hash_algorithm": algorithm.value,
            "metadata": metadata or {},
        }
        record_id = cls.compute_content_hash(record_payload, algorithm)
        return cls(record_id=record_id, subject_id=subject_id, subject_type=subject_type,
                   action=action, actor_id=actor_id, parent_ids=parent_ids or [],
                   content_hash=content_hash, hash_algorithm=algorithm,
                   metadata=metadata or {}, signature=signature)

class ProvenanceChain(BaseModel):
    root_subject_id: str
    records: List[ProvenanceRecord]
    verified: bool = False
    verification_notes: List[str] = Field(default_factory=list)

class ProvenanceSync:
    def __init__(self):
        self._records: Dict[str, ProvenanceRecord] = {}
        self._children: Dict[str, Set[str]] = {}
        self._by_subject: Dict[str, List[str]] = {}

    def record(self, prov):
        if prov.record_id in self._records:
            return self._records[prov.record_id]
        self._records[prov.record_id] = prov
        self._by_subject.setdefault(prov.subject_id, []).append(prov.record_id)
        for pid in prov.parent_ids:
            self._children.setdefault(pid, set()).add(prov.record_id)
        return prov

    def build_chain(self, subject_id, max_depth=50):
        visited, ordered, notes = set(), [], []
        frontier = list(self._by_subject.get(subject_id, []))
        depth = 0
        while frontier and depth < max_depth:
            next_f = []
            for rid in frontier:
                if rid in visited: continue
                visited.add(rid)
                rec = self._records.get(rid)
                if not rec:
                    notes.append(f"Missing {rid}"); continue
                ordered.append(rec)
                next_f.extend(rec.parent_ids)
            frontier = next_f
            depth += 1
        ordered.reverse()
        chain = ProvenanceChain(root_subject_id=subject_id, records=ordered, verification_notes=notes)
        seen = set()
        ok = True
        for rec in chain.records:
            if rec.record_id in seen:
                notes.append(f"Cycle at {rec.record_id}"); ok = False; break
            seen.add(rec.record_id)
            for pid in rec.parent_ids:
                if pid not in self._records:
                    notes.append(f"Dangling parent {pid}"); ok = False
        chain.verified = ok and len(notes) == 0
        return chain

    def export_evidence_package(self, subject_id):
        chain = self.build_chain(subject_id)
        return {
            "subject_id": subject_id, "verified": chain.verified,
            "record_count": len(chain.records),
            "records": [r.model_dump(mode="json") for r in chain.records],
            "verification_notes": chain.verification_notes,
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }
