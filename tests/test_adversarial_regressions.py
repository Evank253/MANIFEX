"""Regression tests for findings in the 2026-10-26 adversarial review.

These tests are intentionally added before implementation fixes. They should fail
against the reviewed baseline and pass only after the corresponding controls land.
"""
import json
import sys

import pytest

from manifex.build_index import AssetRecord, BuildIndex
from manifex.execution_evidence import (
    ExecutionRegistrationError,
    canonical_hash,
    register_execution_evidence,
    validate_packet,
)


def packet(**changes):
    request_payload = {"request_id": "req-1", "mission_id": "mission-1", "command": [sys.executable, "-c", "print('ok')"]}
    result_payload = {"execution_id": "exec-1", "status": "EXECUTED", "exit_code": 0}
    evidence = {
        "evidence_id": "evidence-1",
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
        "exit_code": 0,
        "qualification_status": "NOT_QUALIFIED",
        "request_payload": request_payload,
        "result_payload": result_payload,
        "request_hash": canonical_hash(request_payload),
        "result_hash": canonical_hash(result_payload),
        "evidence_hash": None,
    }
    evidence.update(changes)
    evidence["evidence_hash"] = canonical_hash({k: v for k, v in evidence.items() if k != "evidence_hash"})
    return {
        "schema": "manifex-execution-evidence/v1",
        "qualification_requested": False,
        "authority_decision_requested": False,
        "evidence": evidence,
    }


@pytest.mark.parametrize("field", ["request_payload", "result_payload"])
def test_missing_payload_cannot_be_replaced_by_caller_supplied_hash(field):
    p = packet()
    p["evidence"].pop(field)
    p["evidence"]["evidence_hash"] = canonical_hash(
        {k: v for k, v in p["evidence"].items() if k != "evidence_hash"}
    )
    with pytest.raises(ExecutionRegistrationError):
        validate_packet(p)


@pytest.mark.parametrize(
    "field,value",
    [
        ("execution_started", "false"),
        ("command", "malicious"),
        ("status", {"state": "EXECUTED"}),
        ("exit_code", "0"),
    ],
)
def test_execution_fact_fields_require_strict_types(field, value):
    p = packet()
    p["evidence"][field] = value
    p["evidence"]["evidence_hash"] = canonical_hash(
        {k: v for k, v in p["evidence"].items() if k != "evidence_hash"}
    )
    with pytest.raises(ExecutionRegistrationError):
        validate_packet(p)


def test_execution_id_cannot_escape_evidence_root(tmp_path):
    p = packet(execution_id="../../escaped")
    p["evidence"]["evidence_hash"] = canonical_hash(
        {k: v for k, v in p["evidence"].items() if k != "evidence_hash"}
    )
    with pytest.raises(ExecutionRegistrationError):
        register_execution_evidence(p, tmp_path)
    assert not (tmp_path.parent / "escaped.json").exists()


def test_not_measured_evidence_cannot_qualify_asset(tmp_path):
    index = BuildIndex(tmp_path)
    record = AssetRecord(
        asset_id="asset-test",
        name="test asset",
        source_repository="example/repo",
        state="INSPECTED",
        evidence_level="NOT_MEASURED",
        verification_status="QUALIFIED",
    )
    index.add(record)
    with pytest.raises(ValueError):
        index.transition(
            "asset-test",
            "QUALIFIED",
            evidence_level="NOT_MEASURED",
            verification_status="QUALIFIED",
        )
