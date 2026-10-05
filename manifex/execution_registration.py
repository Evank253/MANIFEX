"""Compatibility exports for MANIFEX execution evidence registration.

The canonical implementation lives in :mod:`manifex.execution_evidence`.
"""
from .execution_evidence import (
    ExecutionEvidenceRecord,
    ExecutionRegistrationError,
    canonical_hash,
    register_execution_evidence,
    validate_packet,
)

__all__ = [
    "ExecutionEvidenceRecord",
    "ExecutionRegistrationError",
    "canonical_hash",
    "register_execution_evidence",
    "validate_packet",
]
