"""Append-only provenance records for MANIFEX acquisitions."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class ProvenanceLedger:
    def __init__(self, path: str | Path = ".manifex/provenance.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, *, source_repository: str, source_commit: str, tree_hash: str,
               copy_id: str, working_copy: str, action: str, modifications: list[str] | None = None) -> dict[str, Any]:
        if not all((source_repository, source_commit, tree_hash, copy_id, working_copy)):
            raise ValueError("complete provenance requires source revision, tree, copy, and working copy")
        event = {
            "timestamp": time.time(), "source_repository": source_repository,
            "source_commit": source_commit, "tree_hash": tree_hash, "copy_id": copy_id,
            "working_copy": working_copy, "action": action,
            "modifications": list(modifications or []),
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, sort_keys=True) + "\n")
        return event
