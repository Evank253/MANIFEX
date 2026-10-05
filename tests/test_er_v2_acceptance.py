"""ER-v2 acceptance tests. Requirements, not prior results.

Each test cites the ER2 requirement it is intended to verify.
Source: docs/ER-V2-REQUIREMENTS-CHANGE-SPECIFICATION.md section 4.
P1-P5 are out of scope.
"""
import json

import pytest

from manifex.execution_evidence import (
    ExecutionRegistrationError,
    canonical_hash,
    register_execution_evidence,
    validate_packet,
    verify_persisted_evidence,
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
        "kronos_only_field": "must-survive-persistence",
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


def test_at1_matching_request_hash_accepted():
    """ER2-R1. Valid request payload + matching request hash is accepted."""
    validate_packet(make_packet())


def test_at2_matching_result_hash_accepted():
    """ER2-R2. Valid result payload + matching result hash is accepted."""
    validate_packet(make_packet())


def test_at3_request_payload_mutation_rejected():
    """ER2-R1. Request payload mutation with unchanged hash is rejected."""
    packet = make_packet()
    packet["evidence"]["request_payload"] = {"request_id": "other"}
    with pytest.raises(ExecutionRegistrationError, match="request hash"):
        validate_packet(packet)


def test_at4_result_payload_mutation_rejected():
    """ER2-R2. Result payload mutation with unchanged hash is rejected."""
    packet = make_packet()
    packet["evidence"]["result_payload"] = {"exit_code": 9}
    with pytest.raises(ExecutionRegistrationError, match="result hash"):
        validate_packet(packet)


def test_at5_missing_request_payload_arbitrary_hash_rejected():
    """ER2-R1, ER2-R5. Missing request payload + arbitrary request hash is rejected."""
    packet = make_packet()
    del packet["evidence"]["request_payload"]
    packet["evidence"]["request_hash"] = "0" * 64
    packet["evidence"]["evidence_hash"] = canonical_hash(
        {k: v for k, v in packet["evidence"].items() if k != "evidence_hash"}
    )
    with pytest.raises(ExecutionRegistrationError, match="request_payload"):
        validate_packet(packet)


def test_at6_missing_result_payload_arbitrary_hash_rejected():
    """ER2-R2, ER2-R5. Missing result payload + arbitrary result hash is rejected."""
    packet = make_packet()
    del packet["evidence"]["result_payload"]
    packet["evidence"]["result_hash"] = "f" * 64
    packet["evidence"]["evidence_hash"] = canonical_hash(
        {k: v for k, v in packet["evidence"].items() if k != "evidence_hash"}
    )
    with pytest.raises(ExecutionRegistrationError, match="result_payload"):
        validate_packet(packet)


def test_at7_missing_both_payloads_recomputed_evidence_hash_rejected():
    """ER2-R1, ER2-R2, ER2-R5. Experiment 001 omitted-payload attack is rejected."""
    packet = make_packet()
    del packet["evidence"]["request_payload"]
    del packet["evidence"]["result_payload"]
    packet["evidence"]["request_hash"] = "0" * 64
    packet["evidence"]["result_hash"] = "f" * 64
    packet["evidence"]["evidence_hash"] = canonical_hash(
        {k: v for k, v in packet["evidence"].items() if k != "evidence_hash"}
    )
    with pytest.raises(ExecutionRegistrationError, match="payload"):
        validate_packet(packet)


def test_at8_persisted_record_recomputes_evidence_hash(tmp_path):
    """ER2-R3, ER2-R4. Persisted evidence reproduces its hash from persisted material only."""
    packet = make_packet()
    register_execution_evidence(packet, tmp_path)
    stored = json.loads((tmp_path / "execution_evidence" / "exec-1.json").read_text())
    verify_persisted_evidence(stored)
    assert stored["evidence_hash"] == canonical_hash(
        {k: v for k, v in stored.items() if k != "evidence_hash"}
    )
    assert stored["request_payload"] == packet["evidence"]["request_payload"]
    assert stored["result_payload"] == packet["evidence"]["result_payload"]
    assert stored["kronos_only_field"] == "must-survive-persistence"


def test_at9_mutation_of_hash_covered_field_detected(tmp_path):
    """ER2-R3. Mutation of any field covered by the evidence hash is detected."""
    packet = make_packet()
    register_execution_evidence(packet, tmp_path)
    stored = json.loads((tmp_path / "execution_evidence" / "exec-1.json").read_text())
    stored["target_commit"] = "tampered"
    with pytest.raises(ExecutionRegistrationError, match="persisted evidence hash"):
        verify_persisted_evidence(stored)


def test_at10_dropped_hash_covered_field_detected(tmp_path):
    """ER2-R3, ER2-R4. Dropping a hash-covered field is detected; registration does not drop fields."""
    packet = make_packet()
    register_execution_evidence(packet, tmp_path)
    stored = json.loads((tmp_path / "execution_evidence" / "exec-1.json").read_text())
    assert "kronos_only_field" in stored
    dropped = dict(stored)
    del dropped["kronos_only_field"]
    with pytest.raises(ExecutionRegistrationError, match="persisted evidence hash"):
        verify_persisted_evidence(dropped)


def test_at11_duplicate_execution_identity_rejected(tmp_path):
    """Duplicate/immutability. Re-registration of the same execution identity is rejected."""
    packet = make_packet()
    register_execution_evidence(packet, tmp_path)
    with pytest.raises(ExecutionRegistrationError, match="already registered"):
        register_execution_evidence(packet, tmp_path)


def test_at12_integrity_pass_does_not_qualify(tmp_path):
    """Qualification boundary. Passing integrity checks cannot promote a record to qualification."""
    record = register_execution_evidence(make_packet(), tmp_path)
    assert record.verification_status == "NOT_QUALIFIED"
    assert record.evidence_level == "NOT_MEASURED"
    assert record.state == "DISCOVERED"
    stored = json.loads((tmp_path / "execution_evidence" / "exec-1.json").read_text())
    assert stored["qualification_status"] == "NOT_QUALIFIED"
    qualified = make_packet()
    qualified["evidence"]["qualification_status"] = "QUALIFIED"
    qualified["evidence"]["evidence_hash"] = canonical_hash(
        {k: v for k, v in qualified["evidence"].items() if k != "evidence_hash"}
    )
    with pytest.raises(ExecutionRegistrationError, match="qualification"):
        validate_packet(qualified)


def test_at13_registration_cannot_request_authority(tmp_path):
    """Authority boundary. Registration cannot create or request consequential authority."""
    packet = make_packet()
    packet["authority_decision_requested"] = True
    with pytest.raises(ExecutionRegistrationError, match="authority"):
        validate_packet(packet)
    record = register_execution_evidence(make_packet(), tmp_path)
    assert record.state == "DISCOVERED"
    assert not (tmp_path / "authority").exists()


def test_v1_schema_is_not_accepted_as_v2():
    """Historical boundary. A frozen v1 packet is not accepted as v2."""
    packet = make_packet()
    packet["schema"] = "manifex-execution-evidence/v1"
    with pytest.raises(ExecutionRegistrationError, match="ER-v1"):
        validate_packet(packet)
