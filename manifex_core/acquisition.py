"""Immutable acquisition planning; execution is deliberately separate."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AcquisitionPlan:
    source_repository: str
    source_commit: str
    tree_hash: str
    destination: str
    copy_id: str
    action: str = "ADAPT"
    modifications: tuple[str, ...] = ()
    approved: bool = False


class AcquisitionEngine:
    """Creates controlled-copy plans without mutating source repositories."""

    @staticmethod
    def make_plan(source_repository: str, source_commit: str, tree_hash: str,
                  destination: str, action: str = "ADAPT") -> AcquisitionPlan:
        if not source_repository or not source_commit or not tree_hash:
            raise ValueError("immutable acquisition requires repository, commit, and tree hash")
        if action not in {"KEEP", "ADAPT", "WRAP", "FREEZE", "BUILD", "REPLACE", "RETIRE"}:
            raise ValueError("invalid MANIFEX action")
        copy_id = "copy-" + hashlib.sha256(
            f"{source_repository}|{source_commit}|{tree_hash}|{destination}".encode()
        ).hexdigest()[:20]
        return AcquisitionPlan(source_repository, source_commit, tree_hash, destination, copy_id, action)

    @staticmethod
    def assert_source_immutable(plan: AcquisitionPlan) -> None:
        """Marker guard for callers: acquisition plans contain no source-write operation."""
        if plan.approved and not plan.source_commit:
            raise ValueError("approved acquisition cannot omit source revision")
