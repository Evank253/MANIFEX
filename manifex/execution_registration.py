"""MANIFEX receiver for Kronos execution evidence.

Registration records evidence; it never qualifies evidence or grants authority.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .build_index import AssetRecord, BuildIndex

SCHEMA = "manifex-execution-evidence/v1"
HASH_FIELDS = ("request_hash", "result_hash", "evidence_hash")
REQUIRED = (
    "evidence_id", "execution_id", "request_id", "mission_id",
    "repository", "target_commit", "provider", "phase", "command",
    "status", "execution_started", "qualification_status",
    *HASH_FIELDS,
)


class ExecutionRegistrationError(ValueError):
    pass


def _sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def validate_packet(packet: Mapping[str, Any]) -> Mapping[str, Any]:
    if packet.get("schema") != SCHEMA:
        raise ExecutionRegistrationError("unsupported evidence schema")
    evidence = packet.get("evidence")
    if not isinstance(evidence, Mapping):
        raise ExecutionRegistrationError("evidence object is required")
    missing = [name for name in REQUIRED if name not in evidence]
    if missing:
        raise ExecutionRegistrationError("missing required fields: " + ", ".join(missing))
    if evidence["qualification_status"] not in {"NOT_QUALIFIED", "NOT_MEASURED"}:
        raise ExecutionRegistrationError("registration cannot carry qualification")
    if packet.get("qualification_requested") is not False:
        raise ExecutionRegistrationError("qualification request must be false")
    if packet.get("authority_decision_requested") is not False:
        raise ExecutionRegistrationError("authority decision request must be false")
    for name in HASH_FIELDS:
        value = evidence[name]
        if not isinstance(value, str) or len(value) != 64:
            raise ExecutionRegistrationError(f"{name} must be SHA-256")
        try:
            int(value, 16)
        except ValueError as exc:
            raise ExecutionRegistrationError(f"{name} must be hexadecimal") from exc
    if not evidence["target_commit"]:
        raise ExecutionRegistrationError("target commit is required")
    return evidence


def register_execution_evidence(packet: Mapping[str, Any], root: Path) -> AssetRecord:
    """Register execution evidence as a discovered MANIFEX asset."""
    evidence = validate_packet(packet)
    index = BuildIndex(root)
    asset_id = index.asset_id(
        evidence["repository"],
        evidence["target_commit"],
        "execution/" + evidence["evidence_id"],
    )
    record = AssetRecord(
        asset_id=asset_id,
        name=f"Kronos execution {evidence['execution_id']}",
        source_repository=evidence["repository"],
        source_commit=evidence["target_commit"],
        source_path="execution/" + evidence["evidence_id"],
        capabilities=[f"execution:{evidence['phase']}"],
        tests=[evidence["command"][0]],
        runtime_status=evidence["status"],
        evidence_level="NOT_MEASURED",
        verification_status=evidence["qualification_status"],
        state="DISCOVERED",
        notes=(
            f"Kronos evidence schema={SCHEMA}; provider={evidence['provider']}; "
            f"request_hash={evidence['request_hash']}; result_hash={evidence['result_hash']}; "
            f"evidence_hash={evidence['evidence_hash']}"
        ),
    )
    return index.add(record)
