from __future__ import annotations
from dataclasses import dataclass, field
from .models import Authorization, CapabilityLease, OperationRequest, SecurityState, Decision
from .engine import ConstitutionalEngine
from .audit import AuditLedger

@dataclass
class ManifexRuntime:
    constitution_hash: str = 'CONSTITUTION-v1'
    audit: AuditLedger = field(default_factory=AuditLedger)
    engine: ConstitutionalEngine = field(init=False)
    state: SecurityState = SecurityState.CREATED
    leases: dict[str, CapabilityLease] = field(default_factory=dict)
    authorizations: dict[str, Authorization] = field(default_factory=dict)

    def __post_init__(self):
        self.audit.constitution_hash = self.constitution_hash
        self.engine = ConstitutionalEngine(self.audit, self.constitution_hash)

    def register_authorization(self, authorization: Authorization) -> None:
        if self.state in {SecurityState.TERMINATED, SecurityState.QUARANTINED}:
            raise PermissionError('runtime is not accepting new authority')
        if authorization.issuer != 'HUMAN' or not authorization.human_authority:
            raise PermissionError('only human authority may issue authorization')
        self.authorizations[authorization.id] = authorization

    def issue_lease(self, authorization_id: str, lease: CapabilityLease) -> CapabilityLease:
        if self.state in {SecurityState.TERMINATED, SecurityState.QUARANTINED, SecurityState.REVOKED}:
            raise PermissionError('runtime is not issuing capability leases')
        auth = self.authorizations.get(authorization_id)
        if not auth or not auth.valid() or lease.authorization_id != authorization_id or lease.subject != auth.subject:
            raise PermissionError('invalid authorization')
        if not lease.capabilities.issubset(auth.capabilities):
            raise PermissionError('lease exceeds authorization')
        if lease.issued_at < auth.issued_at or lease.expires_at > auth.expires_at:
            raise PermissionError('lease lifetime exceeds authorization')
        self.leases[lease.id] = lease
        self.state = SecurityState.AUTHORIZED
        return lease

    def revoke_lease(self, lease_id: str) -> None:
        lease = self.leases.get(lease_id)
        if lease:
            object.__setattr__(lease, 'revoked', True)
        self.state = SecurityState.REVOKED
        self.audit.append(event_id=f'revoke-{lease_id}', event_type='REVOCATION', actor='HUMAN',
                          request_id=None, authorization_id=lease.authorization_id if lease else None,
                          capability_lease_id=lease_id, action='revoke', state_before=SecurityState.AUTHORIZED.value,
                          state_after=SecurityState.REVOKED.value, decision=Decision.ALLOW.value, result='REVOKED',
                          reason='human_revocation')

    def decide(self, request: OperationRequest, authorization_id: str | None = None, lease_id: str | None = None,
               verifier: str | None = None):
        if self.state in {SecurityState.TERMINATED, SecurityState.QUARANTINED}:
            self.audit.append(event_id=f'audit-{request.request_id}', event_type='DECISION', actor=request.actor,
                              request_id=request.request_id, authorization_id=authorization_id,
                              capability_lease_id=lease_id, action=request.action,
                              state_before=self.state.value, state_after=SecurityState.DENIED.value,
                              decision=Decision.DENY.value, result='BLOCKED', reason='runtime_not_operational')
            from .models import DecisionRecord
            return DecisionRecord(request.request_id, Decision.DENY, 'runtime_not_operational', ('EXEC-001',))
        auth = self.authorizations.get(authorization_id) if authorization_id else None
        lease = self.leases.get(lease_id) if lease_id else None
        if auth and auth.subject != request.actor:
            from .models import DecisionRecord
            return DecisionRecord(request.request_id, Decision.DENY, 'identity_scope_mismatch', ('AUTH-001',))
        if lease and lease.subject != request.actor:
            from .models import DecisionRecord
            return DecisionRecord(request.request_id, Decision.DENY, 'lease_subject_mismatch', ('AUTH-001',))
        return self.engine.decide(request, auth, lease, verifier=verifier)

    def emergency_stop(self) -> None:
        self.leases.clear()
        self.state = SecurityState.TERMINATED
        self.audit.append(event_id='emergency-stop', event_type='EMERGENCY_STOP', actor='HUMAN',
                          request_id=None, authorization_id=None, capability_lease_id=None, action='terminate_all',
                          state_before=SecurityState.RUNNING.value, state_after=SecurityState.TERMINATED.value,
                          decision=Decision.ALLOW.value, result='TERMINATED', reason='human_emergency_stop')
