import hashlib
import json

import pytest

from manifex.execution_evidence import (
    ExecutionRegistrationError,
    canonical_hash,
    register_execution_evidence,
    validate_packet,
)


def make_packet(**changes):
    request_payload = {"request_id": "req-1", "mission_id": "mission-1", "command": ["python", "-c", "print('ok')"]}
    result_payload = {"execution_id": "exec-1", "status": "EXECUTED", "exit_code": 0}
    evidence = {
        "evidence_id": "exec-exec-1",
        "execution_id": "exec-1",
        "request_id": "req-1",
        "mission_id": "mission-1",
        "repository": "example/repo",
        "target_commit": "abc123",
        "provider": "local",
        "provider_run_id": "local-1",
        "phase": "test",
        "command": ["python", "-c", "print('ok')"],
        "status": "EXECUTED",
        "execution_started": True,
        "exit_code": 0,
        "failure_class": None,
        "environment": {"python": "3.13"},
        "started_at": "2026-10-04T00:00:00Z",
        "finished_at": "2026-10-04T00:00:01Z",
        "request_payload": request_payload,
        "result_payload": result_payload,
        "request_hash": canonical_hash(request_payload),
        "result_hash": canonical_hash(result_payload),
        "evidence_hash": None,
        "qualification_status": "NOT_QUALIFIED",
    }
    evidence.update(changes)
    evidence["evidence_hash"] = canonical_hash({k: v for k, v in evidence.items() if k != "evidence_hash"})
    return {
        "schema": "manifex-execution-evidence/v2",
        "source": "Kronos-Vibe-Coder",
        "qualification_requested": False,
        "authority_decision_requested": False,
        "evidence": evidence,
    }


def test_valid_evidence_persists_first_class_fields(tmp_path):
    packet = make_packet()
    register_execution_evidence(packet, tmp_path)
    stored = json.loads((tmp_path / "execution_evidence" / "exec-1.json").read_text())
    for field in (
        "execution_id", "request_id", "mission_id", "repository", "target_commit",
        "provider", "provider_run_id", "phase", "command", "status",
        "execution_started", "exit_code", "failure_class", "environment",
        "started_at", "finished_at", "request_hash", "result_hash",
        "evidence_hash", "qualification_status",
    ):
        assert field in stored


@pytest.mark.parametrize("field", ["evidence_hash", "request_hash", "result_hash"])
def test_tampered_hash_is_rejected(tmp_path, field):
    packet = make_packet()
    packet["evidence"][field] = "f" * 64
    with pytest.raises(ExecutionRegistrationError):
        validate_packet(packet)


def test_not_measured_and_not_qualified_survive_registration(tmp_path):
    packet = make_packet()
    packet["evidence"]["status"] = "NOT_MEASURED"
    packet["evidence"]["qualification_status"] = "NOT_MEASURED"
    packet["evidence"]["evidence_hash"] = canonical_hash(
        {k: v for k, v in packet["evidence"].items() if k != "evidence_hash"}
    )
    record = register_execution_evidence(packet, tmp_path)
    assert record.evidence_level == "NOT_MEASURED"
    assert record.verification_status == "NOT_MEASURED"


def test_failed_execution_is_preserved_as_failure(tmp_path):
    packet = make_packet()
    packet["evidence"].update({"status": "FAILED", "failure_class": "TEST_FAILED", "exit_code": 3})
    packet["evidence"]["evidence_hash"] = canonical_hash(
        {k: v for k, v in packet["evidence"].items() if k != "evidence_hash"}
    )
    record = register_execution_evidence(packet, tmp_path)
    assert record.runtime_status == "FAILED"
    assert record.verification_status == "NOT_QUALIFIED"


def test_duplicate_execution_id_cannot_overwrite(tmp_path):
    packet = make_packet()
    register_execution_evidence(packet, tmp_path)
    with pytest.raises(ExecutionRegistrationError):
        register_execution_evidence(packet, tmp_path)


@pytest.mark.parametrize("field,value", [
    ("qualification_requested", True),
    ("authority_decision_requested", True),
])
def test_registration_cannot_request_qualification_or_authority(tmp_path, field, value):
    packet = make_packet()
    packet[field] = value
    with pytest.raises(ExecutionRegistrationError):
        validate_packet(packet)


def test_registration_ledger_records_event(tmp_path):
    register_execution_evidence(make_packet(), tmp_path)
    lines = (tmp_path / "execution_evidence_ledger.jsonl").read_text().splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["event"] == "EXECUTION_EVIDENCE_REGISTERED"
    assert event["execution_id"] == "exec-1"
    assert event["target_commit"] == "abc123"


def test_request_and_result_hashes_are_recomputed(tmp_path):
    packet = make_packet()
    packet["evidence"]["request_payload"]["mission_id"] = "tampered"
    with pytest.raises(ExecutionRegistrationError):
        validate_packet(packet)

    packet = make_packet()
    packet["evidence"]["result_payload"]["exit_code"] = 9
    with pytest.raises(ExecutionRegistrationError):
        validate_packet(packet)
