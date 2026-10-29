"""First-class MANIFEX storage and integrity validation for execution evidence.

Registration records facts only. It never grants authority or qualification.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from .build_index import AssetRecord, BuildIndex

SCHEMA = "manifex-execution-evidence/v1"
HASH_FIELDS = ("request_hash", "result_hash", "evidence_hash")
REQUIRED = (
    "evidence_id", "execution_id", "request_id", "mission_id",
    "repository", "target_commit", "provider", "phase", "command",
    "status", "execution_started", "qualification_status", *HASH_FIELDS,
)
FIRST_CLASS_FIELDS = (
    "evidence_id", "execution_id", "request_id", "mission_id", "repository",
    "target_commit", "provider", "provider_run_id", "phase", "command", "status",
    "execution_started", "exit_code", "failure_class", "environment",
    "started_at", "finished_at", "request_payload", "result_payload",
    "request_hash", "result_hash", "evidence_hash", "qualification_status",
)
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class ExecutionRegistrationError(ValueError):
    """Raised when an execution evidence packet is incomplete or invalid."""


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
    request_payload: Mapping[str, Any]
    result_payload: Mapping[str, Any]
    provider_run_id: Optional[str] = None
    exit_code: Optional[int] = None
    failure_class: Optional[str] = None
    environment: Mapping[str, Any] = field(default_factory=dict)
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value) is not None


def _expected_evidence_hash(evidence: Mapping[str, Any]) -> str:
    return canonical_hash({k: v for k, v in evidence.items() if k != "evidence_hash"})


def validate_packet(packet: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(packet, Mapping) or packet.get("schema") != SCHEMA:
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
        if not _is_sha256(evidence[name]):
            raise ExecutionRegistrationError(f"{name} must be a 64-character SHA-256 hex digest")

    for name in ("evidence_id", "execution_id", "request_id", "mission_id", "repository",
                 "target_commit", "provider", "phase", "status"):
        if not isinstance(evidence.get(name), str) or not evidence[name].strip():
            raise ExecutionRegistrationError(f"{name} must be a non-empty string")
    if not _SAFE_ID.fullmatch(evidence["execution_id"]):
        raise ExecutionRegistrationError("execution_id must be a safe single path component")
    if not isinstance(evidence.get("command"), list) or not evidence["command"] or not all(
        isinstance(part, str) and part for part in evidence["command"]
    ):
        raise ExecutionRegistrationError("command must be a non-empty list of non-empty strings")
    if not isinstance(evidence.get("execution_started"), bool):
        raise ExecutionRegistrationError("execution_started must be a boolean")
    if "exit_code" in evidence and evidence["exit_code"] is not None and (
        isinstance(evidence["exit_code"], bool) or not isinstance(evidence["exit_code"], int)
    ):
        raise ExecutionRegistrationError("exit_code must be an integer or null")
    if "environment" in evidence and not isinstance(evidence["environment"], Mapping):
        raise ExecutionRegistrationError("environment must be an object")
    if not isinstance(evidence.get("request_payload"), Mapping):
        raise ExecutionRegistrationError("request_payload object is required")
    if not isinstance(evidence.get("result_payload"), Mapping):
        raise ExecutionRegistrationError("result_payload object is required")
    if canonical_hash(evidence["request_payload"]) != evidence["request_hash"]:
        raise ExecutionRegistrationError("request hash does not match request payload")
    if canonical_hash(evidence["result_payload"]) != evidence["result_hash"]:
        raise ExecutionRegistrationError("result hash does not match result payload")
    if evidence["evidence_hash"] != _expected_evidence_hash(evidence):
        raise ExecutionRegistrationError("evidence hash does not match evidence payload")
    return evidence


def _record_from_evidence(evidence: Mapping[str, Any]) -> ExecutionEvidenceRecord:
    return ExecutionEvidenceRecord(**{
        name: evidence.get(name)
        for name in FIRST_CLASS_FIELDS
    })


def register_execution_evidence(packet: Mapping[str, Any], root: Path) -> AssetRecord:
    """Validate and register evidence as DISCOVERED; never qualify or authorize it."""
    evidence = validate_packet(packet)
    evidence_record = _record_from_evidence(evidence)
    root = Path(root).resolve()
    evidence_root = root / "execution_evidence"
    evidence_root.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_root / f"{evidence_record.execution_id}.json"

    # Exclusive create prevents overwrites and closes the simple duplicate-ID race.
    try:
        with evidence_path.open("x", encoding="utf-8") as fh:
            json.dump(asdict(evidence_record), fh, sort_keys=True, indent=2)
            fh.write("\n")
            fh.flush()
    except FileExistsError as exc:
        raise ExecutionRegistrationError(
            f"execution evidence already registered: {evidence_record.execution_id}"
        ) from exc

    index = BuildIndex(root)
    asset_id = index.asset_id(
        evidence_record.repository, evidence_record.target_commit,
        "execution/" + evidence_record.evidence_id,
    )
    record = AssetRecord(
        asset_id=asset_id,
        name=f"Execution {evidence_record.execution_id}",
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
        index.add(record)
        with (root / "execution_evidence_ledger.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "event": "EXECUTION_EVIDENCE_REGISTERED",
                "evidence_id": evidence_record.evidence_id,
                "execution_id": evidence_record.execution_id,
                "request_id": evidence_record.request_id,
                "mission_id": evidence_record.mission_id,
                "target_commit": evidence_record.target_commit,
                "evidence_hash": evidence_record.evidence_hash,
            }, sort_keys=True) + "\n")
    except Exception:
        # Best-effort compensation. The independent ledgers still need a durable
        # transaction/recovery design for crash consistency and concurrent writers.
        evidence_path.unlink(missing_ok=True)
        raise
    return record
