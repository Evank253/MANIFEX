#!/usr/bin/env python3
"""MANIFEX Build Index — provenance-first asset registry.

Purpose:
    Give MANIFEX a durable index for assets discovered across projects.

Design rules:
    - Source repositories are never modified by this module.
    - Every asset carries source revision/provenance metadata.
    - Discovery does not imply approval or reuse.
    - State transitions are explicit and append-only in the event ledger.
    - Missing evidence remains NOT_MEASURED rather than being inferred.

State flow:
    DISCOVERED -> INSPECTED -> QUALIFIED -> APPROVED -> IMPORTED -> VERIFIED -> REUSABLE

This is intentionally dependency-free so it can run inside the MANIFEX working copy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


STATES = (
    "DISCOVERED",
    "INSPECTED",
    "QUALIFIED",
    "APPROVED",
    "IMPORTED",
    "VERIFIED",
    "REUSABLE",
)

ACTIONS = (
    "KEEP",
    "ADAPT",
    "WRAP",
    "FREEZE",
    "BUILD",
    "REPLACE",
    "RETIRE",
)

EVIDENCE_LEVELS = {"E0", "E1", "E2", "E3", "E4", "E5", "NOT_MEASURED"}

_ALLOWED_TRANSITIONS = {
    "DISCOVERED": {"INSPECTED"},
    "INSPECTED": {"QUALIFIED"},
    "QUALIFIED": {"APPROVED"},
    "APPROVED": {"IMPORTED"},
    "IMPORTED": {"VERIFIED"},
    "VERIFIED": {"REUSABLE"},
}


@dataclass
class AssetRecord:
    asset_id: str
    name: str
    source_repository: str
    source_branch: str = ""
    source_commit: str = ""
    tree_hash: str = ""
    source_path: str = ""
    source_license: str = "NOT_MEASURED"
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    tests: List[str] = field(default_factory=list)
    runtime_status: str = "NOT_MEASURED"
    evidence_level: str = "NOT_MEASURED"
    manifex_action: str = "ADAPT"
    copy_id: str = ""
    working_copy: str = ""
    modifications: List[str] = field(default_factory=list)
    verification_status: str = "NOT_MEASURED"
    state: str = "DISCOVERED"
    notes: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def validate(self) -> None:
        if not self.asset_id or not self.name or not self.source_repository:
            raise ValueError("asset_id, name, and source_repository are required")
        if self.state not in STATES:
            raise ValueError(f"invalid state: {self.state}")
        if self.manifex_action not in ACTIONS:
            raise ValueError(f"invalid MANIFEX action: {self.manifex_action}")
        if self.evidence_level not in EVIDENCE_LEVELS:
            raise ValueError(f"invalid evidence level: {self.evidence_level}")


class BuildIndex:
    """JSONL-backed registry plus append-only transition ledger."""

    def __init__(self, root: Path):
        self.root = root
        self.index_path = root / "build_index.jsonl"
        self.ledger_path = root / "build_index_ledger.jsonl"
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def asset_id(source_repository: str, source_commit: str, source_path: str) -> str:
        raw = f"{source_repository}|{source_commit}|{source_path}".encode()
        return "asset-" + hashlib.sha256(raw).hexdigest()[:20]

    def _read_records(self) -> Dict[str, AssetRecord]:
        records: Dict[str, AssetRecord] = {}
        if not self.index_path.exists():
            return records
        for line in self.index_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            record = AssetRecord(**data)
            records[record.asset_id] = record
        return records

    def _append_index(self, record: AssetRecord) -> None:
        with self.index_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(record), sort_keys=True) + "\n")

    def _append_event(self, event: Dict[str, Any]) -> None:
        event = dict(event)
        event["timestamp"] = time.time()
        with self.ledger_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, sort_keys=True) + "\n")

    def add(self, record: AssetRecord) -> AssetRecord:
        record.validate()
        records = self._read_records()
        if record.asset_id in records:
            raise ValueError(f"asset already indexed: {record.asset_id}")
        self._append_index(record)
        self._append_event({
            "event": "ASSET_DISCOVERED",
            "asset_id": record.asset_id,
            "source_repository": record.source_repository,
            "source_commit": record.source_commit,
            "source_path": record.source_path,
            "state": record.state,
        })
        return record

    def get(self, asset_id: str) -> Optional[AssetRecord]:
        return self._read_records().get(asset_id)

    def transition(self, asset_id: str, new_state: str, evidence_level: Optional[str] = None,
                   verification_status: Optional[str] = None, notes: Optional[str] = None) -> AssetRecord:
        if new_state not in STATES:
            raise ValueError(f"invalid state: {new_state}")
        records = self._read_records()
        record = records.get(asset_id)
        if record is None:
            raise KeyError(asset_id)
        if new_state == record.state:
            return record
        if new_state not in _ALLOWED_TRANSITIONS.get(record.state, set()):
            raise ValueError(f"invalid transition: {record.state} -> {new_state}")
        if evidence_level is not None and evidence_level not in EVIDENCE_LEVELS:
            raise ValueError(f"invalid evidence level: {evidence_level}")

        updated = AssetRecord(**asdict(record))
        updated.state = new_state
        updated.updated_at = time.time()
        if evidence_level is not None:
            updated.evidence_level = evidence_level
        if verification_status is not None:
            updated.verification_status = verification_status
        if notes is not None:
            updated.notes = notes

        # JSONL is append-only; latest record wins when rebuilding the index.
        self._append_index(updated)
        self._append_event({
            "event": "STATE_TRANSITION",
            "asset_id": asset_id,
            "from": record.state,
            "to": new_state,
            "evidence_level": updated.evidence_level,
            "verification_status": updated.verification_status,
        })
        return updated

    def list(self, state: Optional[str] = None, action: Optional[str] = None) -> List[AssetRecord]:
        records = list(self._read_records().values())
        if state:
            records = [r for r in records if r.state == state]
        if action:
            records = [r for r in records if r.manifex_action == action]
        return sorted(records, key=lambda r: r.name.lower())

    def summary(self) -> Dict[str, Any]:
        records = self.list()
        by_state = {state: sum(r.state == state for r in records) for state in STATES}
        by_action = {action: sum(r.manifex_action == action for r in records) for action in ACTIONS}
        return {
            "asset_count": len(records),
            "by_state": by_state,
            "by_action": by_action,
            "index": str(self.index_path),
            "ledger": str(self.ledger_path),
        }


def _parse_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()] if value else []


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="MANIFEX Build Index")
    parser.add_argument("--root", default=".manifex", help="MANIFEX registry directory")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="register a discovered asset")
    add.add_argument("--name", required=True)
    add.add_argument("--repo", required=True, dest="source_repository")
    add.add_argument("--branch", default="")
    add.add_argument("--commit", default="")
    add.add_argument("--tree", default="")
    add.add_argument("--path", default="")
    add.add_argument("--license", default="NOT_MEASURED", dest="source_license")
    add.add_argument("--capabilities", default="")
    add.add_argument("--dependencies", default="")
    add.add_argument("--interfaces", default="")
    add.add_argument("--tests", default="")
    add.add_argument("--evidence", default="NOT_MEASURED", choices=sorted(EVIDENCE_LEVELS))
    add.add_argument("--action", default="ADAPT", choices=ACTIONS, dest="manifex_action")
    add.add_argument("--runtime", default="NOT_MEASURED", dest="runtime_status")
    add.add_argument("--notes", default="")

    transition = sub.add_parser("transition", help="advance an asset through the qualification gate")
    transition.add_argument("asset_id")
    transition.add_argument("state", choices=STATES)
    transition.add_argument("--evidence", choices=sorted(EVIDENCE_LEVELS))
    transition.add_argument("--verification")
    transition.add_argument("--notes")

    listing = sub.add_parser("list", help="list indexed assets")
    listing.add_argument("--state", choices=STATES)
    listing.add_argument("--action", choices=ACTIONS)

    sub.add_parser("summary", help="show registry summary")
    args = parser.parse_args(argv)
    index = BuildIndex(Path(args.root))

    if args.command == "add":
        aid = index.asset_id(args.source_repository, args.commit, args.path)
        record = AssetRecord(
            asset_id=aid,
            name=args.name,
            source_repository=args.source_repository,
            source_branch=args.branch,
            source_commit=args.commit,
            tree_hash=args.tree,
            source_path=args.path,
            source_license=args.source_license,
            capabilities=_parse_csv(args.capabilities),
            dependencies=_parse_csv(args.dependencies),
            interfaces=_parse_csv(args.interfaces),
            tests=_parse_csv(args.tests),
            runtime_status=args.runtime_status,
            evidence_level=args.evidence,
            manifex_action=args.manifex_action,
            notes=args.notes,
        )
        print(json.dumps(asdict(index.add(record)), indent=2, sort_keys=True))
        return 0

    if args.command == "transition":
        record = index.transition(args.asset_id, args.state, args.evidence, args.verification, args.notes)
        print(json.dumps(asdict(record), indent=2, sort_keys=True))
        return 0

    if args.command == "list":
        for record in index.list(args.state, args.action):
            print(f"{record.asset_id}\t{record.state}\t{record.manifex_action}\t{record.name}")
        return 0

    print(json.dumps(index.summary(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
