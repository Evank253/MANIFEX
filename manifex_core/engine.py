from __future__ import annotations
from dataclasses import dataclass
from .models import Authorization, CapabilityLease, Decision, DecisionRecord, OperationRequest, SecurityState
from .audit import AuditLedger

INVARIANTS = {
    "HUMAN-001": "human_final_authority",
    "AUTH-001": "ai_cannot_grant_itself_authority",
    "AUTH-002": "authority_is_non_transitive",
    "AUTH-003": "ai_action_cannot_increase_ai_authority",
    "EXEC-001": "no_valid_authorization_no_execution",
    "EXEC-002": "expired_lease_has_zero_capability",
    "SEC-001": "ai_cannot_modify_safety_kernel",
    "SEC-002": "ai_cannot_disable_audit",
    "SEC-003": "ai_cannot_disable_shutdown",
    "GOV-001": "ai_cannot_modify_active_constitution",
    "VERIFY-001": "actor_cannot_solely_certify_own_consequential_action",
    "HUMAN-002": "authorized_human_can_revoke",
    "HUMAN-003": "authorized_human_can_terminate",
    "AUDIT-001": "consequential_actions_are_auditable",
    "AUDIT-002": "audit_records_are_append_only",
    "AUDIT-003": "audit_history_is_integrity_protected",
    "AUDIT-004": "ai_cannot_disable_audit",
    "AUDIT-005": "ai_cannot_modify_audit_history",
    "AUDIT-006": "consequential_action_has_provenance",
    "AUDIT-007": "security_events_cannot_be_silently_discarded",
    "AUDIT-008": "human_authority_events_are_auditable",
}

@dataclass
class ConstitutionalEngine:
    audit: AuditLedger
    constitution_hash: str = "CONSTITUTION-v1"

    def decide(self, request: OperationRequest, authorization: Authorization | None = None,
               lease: CapabilityLease | None = None, *, verifier: str | None = None) -> DecisionRecord:
        critical = []
        reason = "authorized"
        if not request.actor:
            return self._deny(request, "missing_actor", ("HUMAN-001",))
        if request.action in {"modify_constitution", "modify_safety_kernel", "disable_audit", "disable_shutdown", "forge_human_approval"}:
            critical = tuple(k for k, v in INVARIANTS.items() if v in {
                "ai_cannot_modify_active_constitution", "ai_cannot_modify_safety_kernel", "ai_cannot_disable_audit", "ai_cannot_disable_shutdown"})
            return self._deny(request, "constitutional_action_forbidden", critical)
        if request.consequential and authorization is None:
            return self._deny(request, "missing_authorization", ("EXEC-001",))
        if authorization and not authorization.valid():
            return self._deny(request, "invalid_or_expired_authorization", ("EXEC-001", "EXEC-002"))
        if authorization and not request.requested_capabilities.issubset(authorization.capabilities):
            return self._deny(request, "capability_scope_exceeded", ("EXEC-001", "AUTH-003"))
        if lease is None or not lease.valid():
            return self._deny(request, "missing_expired_or_revoked_lease", ("EXEC-001", "EXEC-002"))
        if not request.requested_capabilities.issubset(lease.capabilities):
            return self._deny(request, "lease_scope_exceeded", ("AUTH-003",))
        if request.consequential and verifier == request.actor:
            return self._deny(request, "self_verification_forbidden", ("VERIFY-001",))
        return DecisionRecord(request.request_id, Decision.ALLOW, reason, tuple(critical), authorization.id if authorization else None, lease.id if lease else None)

    def _deny(self, request: OperationRequest, reason: str, invariants: tuple[str, ...]) -> DecisionRecord:
        self.audit.append(event_id=f"audit-{request.request_id}", event_type="DECISION", actor=request.actor,
                          request_id=request.request_id, authorization_id=None, capability_lease_id=None,
                          action=request.action, state_before=SecurityState.CREATED.value, state_after=SecurityState.DENIED.value,
                          decision=Decision.DENY.value, result="BLOCKED", reason=reason)
        return DecisionRecord(request.request_id, Decision.DENY, reason, invariants)
