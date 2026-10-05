import sys

import pytest

from manifex.execution_registration import (
    ExecutionRegistrationError,
    register_execution_evidence,
    validate_packet,
)


def packet():
    return {
        "schema": "manifex-execution-evidence/v1",
        "source": "Kronos-Vibe-Coder",
        "qualification_requested": False,
        "authority_decision_requested": False,
        "evidence": {
            "evidence_id": "exec-1",
            "execution_id": "exec-1",
            "request_id": "req-1",
            "mission_id": "mission-1",
            "repository": "example/repo",
            "target_commit": "abc123",
            "provider": "local",
            "phase": "test",
            "command": [sys.executable, "-c", "print('ok')"],
            "status": "EXECUTED",
            "execution_started": True,
            "qualification_status": "NOT_QUALIFIED",
            "request_hash": "a" * 64,
            "result_hash": "b" * 64,
            "evidence_hash": "c" * 64,
        },
    }


def test_valid_packet_registers_as_discovered(tmp_path):
    record = register_execution_evidence(packet(), tmp_path)
    assert record.state == "DISCOVERED"
    assert record.evidence_level == "NOT_MEASURED"
    assert record.verification_status == "NOT_QUALIFIED"


def test_receiver_rejects_qualification(tmp_path):
    p = packet()
    p["evidence"]["qualification_status"] = "QUALIFIED"
    with pytest.raises(ExecutionRegistrationError):
        validate_packet(p)


def test_receiver_rejects_authority_request(tmp_path):
    p = packet()
    p["authority_decision_requested"] = True
    with pytest.raises(ExecutionRegistrationError):
        validate_packet(p)


def test_receiver_rejects_bad_hash(tmp_path):
    p = packet()
    p["evidence"]["evidence_hash"] = "bad"
    with pytest.raises(ExecutionRegistrationError):
        validate_packet(p)


def test_receiver_rejects_missing_commit(tmp_path):
    p = packet()
    p["evidence"]["target_commit"] = ""
    with pytest.raises(ExecutionRegistrationError):
        validate_packet(p)
