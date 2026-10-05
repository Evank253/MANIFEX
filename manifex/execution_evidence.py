"""First-class MANIFEX storage and integrity validation for Kronos execution evidence.

ER-v2 (ER-V2-REQ-001). Registration preserves execution facts; it never qualifies
evidence or grants authority.

Requirements implemented:
- ER2-R1 / ER2-R2: unconditional request/result hash binding
- ER2-R3 / ER2-R4: persisted object is the hashed evidence object
- ER2-R5: fail closed on missing binding material

ER-v1 schema packets are rejected. The frozen v1 checkpoint is not modified.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from .build_index import AssetRecord, BuildIndex

SCHEMA = "manifex-execution-evidence/v2"
FROZEN_V1_SCHEMA = "manifex-execution-evidence/v1"
HASH_FIELDS = ("request_hash", "result_hash", "evidence_hash")
REQUIRED = (
    "evidence_id", "execution_id", "request_id", "mission_id",
    "repository", "target_commit", "provider", "phase", "command",
    "status", "execution_started", "qualification_status",
    "request_payload", "result_payload",
    *HASH_FIELDS,
)
INDEX_FIELDS = (
    "evidence_id", "execution_id", "request_id", "mission_id", "repository", "target_commit",
    "provider", "provider_run_id", "phase", "command", "status",
    "execution_started", "exit_code", "failure_class", "environment",
    "started_at", "finished_at", "request_hash", "result_hash",
    "evidence_hash", "qualification_status",
)


class ExecutionRegistrationError(ValueError):
    pass


@dataclass
class ExecutionEvidenceRecord:
    evidence_id: str
    execution_id: str
    request_id: str
    mission_id: str
    repository: str
    target_commit: str
    provider: str
    phase: str
    command: list[str]
    status: str
    execution_started: bool
    qualification_status: str
    request_hash: str
    result_hash: str
    evidence_hash: str
    provider_run_id: Optional[str] = None
    exit_code: Optional[int] = None
    failure_class: Optional[str] = None
    environment: Mapping[str, Any] = field(default_factory=dict)
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(payload).hexdigest()


def _hash_matches(value: str, expected: Any) -> bool:
    return value == canonical_hash(expected)


def _expected_evidence_hash(evidence: Mapping[str, Any]) -> str:
    hash_input = {k: v for k, v in evidence.items() if k != "evidence_hash"}
    return canonical_hash(hash_input)


def _require_sha256(name: str, value: Any) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ExecutionRegistrationError(f"{name} must be SHA-256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ExecutionRegistrationError(f"{name} must be hexadecimal") from exc


def _require_payload(name: str, evidence: Mapping[str, Any]) -> Any:
    if name not in evidence or evidence[name] is None:
        raise ExecutionRegistrationError(
            f"{name} is required; a hash without its payload is not binding"
        )
    payload = evidence[name]
    try:
        canonical_hash(payload)
    except (TypeError, ValueError) as exc:
        raise ExecutionRegistrationError(f"{name} is malformed and cannot be hashed") from exc
    return payload


def validate_packet(packet: Mapping[str, Any]) -> Mapping[str, Any]:
    schema = packet.get("schema")
    if schema == FROZEN_V1_SCHEMA:
        raise ExecutionRegistrationError("ER-v1 schema is frozen and is not accepted as ER-v2")
    if schema != SCHEMA:
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
        raise ExecutionRegistrationError("authority decision must be false")
    for name in HASH_FIELDS:
        _require_sha256(name, evidence[name])
    if not evidence["target_commit"]:
        raise ExecutionRegistrationError("target commit is required")

    request_payload = _require_payload("request_payload", evidence)
    result_payload = _require_payload("result_payload", evidence)
    if not _hash_matches(evidence["request_hash"], request_payload):
        raise ExecutionRegistrationError("request hash does not match request payload")
    if not _hash_matches(evidence["result_hash"], result_payload):
        raise ExecutionRegistrationError("result hash does not match result payload")

    expected_evidence = _expected_evidence_hash(evidence)
    if evidence["evidence_hash"] != expected_evidence:
        raise ExecutionRegistrationError("evidence hash does not match evidence payload")
    return evidence


def verify_persisted_evidence(record: Mapping[str, Any]) -> None:
    """Recompute evidence_hash from the persisted object alone. Fail closed. ER2-R3."""
    if not isinstance(record, Mapping) or "evidence_hash" not in record:
        raise ExecutionRegistrationError("persisted evidence is missing evidence_hash")
    _require_sha256("evidence_hash", record["evidence_hash"])
    request_payload = _require_payload("request_payload", record)
    result_payload = _require_payload("result_payload", record)
    if "request_hash" not in record or not _hash_matches(record["request_hash"], request_payload):
        raise ExecutionRegistrationError("persisted request hash does not match request payload")
    if "result_hash" not in record or not _hash_matches(record["result_hash"], result_payload):
        raise ExecutionRegistrationError("persisted result hash does not match result payload")
    if record["evidence_hash"] != _expected_evidence_hash(record):
        raise ExecutionRegistrationError("persisted evidence hash does not match persisted object")


def _index_record(evidence: Mapping[str, Any]) -> ExecutionEvidenceRecord:
    values = {name: evidence.get(name) for name in INDEX_FIELDS if name in evidence}
    return ExecutionEvidenceRecord(**values)


def register_execution_evidence(packet: Mapping[str, Any], root: Path) -> AssetRecord:
    """Validate and register execution evidence as a discovered MANIFEX asset.

    Persists the hashed evidence object, not a field projection. ER2-R3 / ER2-R4.
    """
    evidence = validate_packet(packet)
    evidence_record = _index_record(evidence)
    evidence_root = root / "execution_evidence"
    evidence_root.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_root / f"{evidence_record.execution_id}.json"
    if evidence_path.exists():
        raise ExecutionRegistrationError(
            f"execution evidence already registered: {evidence_record.execution_id}"
        )
    persisted = dict(evidence)
    evidence_path.write_text(
        json.dumps(persisted, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    try:
        verify_persisted_evidence(json.loads(evidence_path.read_text(encoding="utf-8")))
    except ExecutionRegistrationError:
        evidence_path.unlink(missing_ok=True)
        raise

    index = BuildIndex(root)
    asset_id = index.asset_id(
        evidence_record.repository,
        evidence_record.target_commit,
        "execution/" + evidence_record.evidence_id,
    )
    record = AssetRecord(
        asset_id=asset_id,
        name=f"Kronos execution {evidence_record.execution_id}",
        source_repository=evidence_record.repository,
        source_commit=evidence_record.target_commit,
        source_path="execution/" + evidence_record.evidence_id,
        capabilities=[f"execution:{evidence_record.phase}"],
        tests=[evidence_record.command[0]],
        runtime_status=evidence_record.status,
        evidence_level="NOT_MEASURED",
        verification_status=evidence_record.qualification_status,
        state="DISCOVERED",
        notes=f"First-class evidence: {evidence_path}",
    )
    try:
        result = index.add(record)
    except Exception:
        evidence_path.unlink(missing_ok=True)
        raise
    with (root / "execution_evidence_ledger.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "event": "EXECUTION_EVIDENCE_REGISTERED",
            "evidence_id": evidence_record.evidence_id,
            "execution_id": evidence_record.execution_id,
            "request_id": evidence_record.request_id,
            "mission_id": evidence_record.mission_id,
            "target_commit": evidence_record.target_commit,
            "evidence_hash": evidence_record.evidence_hash,
            "schema": SCHEMA,
        }, sort_keys=True) + "\n")
    return result
