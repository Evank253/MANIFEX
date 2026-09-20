from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, FrozenSet

from .containment import ContainmentEnforcer
from .identity import ExecutionIdentity
from .models import Decision, OperationRequest, SecurityState
from .runtime import ManifexRuntime
from .sandbox import SandboxRunner, SandboxUnavailable


@dataclass(frozen=True)
class LLMManifest:
    manifest_id: str
    model_id: str
    version: str
    allowed_actions: FrozenSet[str] = frozenset()
    allowed_capabilities: FrozenSet[str] = frozenset()
    environment: str = 'sandbox'


@dataclass
class ManifestExecutor:
    """Routes manifest requests through identity, Core, containment, then execution."""

    runtime: ManifexRuntime
    manifest: LLMManifest
    containment: ContainmentEnforcer = field(default_factory=ContainmentEnforcer)
    identity: ExecutionIdentity | None = None
    sandbox: SandboxRunner | None = None

    def bind_identity(self, identity: ExecutionIdentity) -> None:
        if not identity.valid_for(identity.subject, self.manifest.manifest_id, self.manifest.environment):
            raise PermissionError('invalid execution identity')
        self.identity = identity

    def _deny(self, actor: str, action: str, reason: str) -> tuple[Decision, object | None]:
        self.runtime.audit.append(
            event_id=f'manifest-deny:{self.manifest.manifest_id}:{action}',
            event_type='MANIFEST_DENIAL',
            actor=actor,
            request_id=f'manifest:{self.manifest.manifest_id}',
            authorization_id=None,
            capability_lease_id=None,
            action=action,
            state_before=self.runtime.state.value,
            state_after=SecurityState.DENIED.value,
            decision=Decision.DENY.value,
            result='BLOCKED',
            reason=reason,
        )
        return Decision.DENY, None

    def request(
        self,
        actor: str,
        action: str,
        purpose: str,
        capabilities: FrozenSet[str],
        authorization_id: str | None = None,
        lease_id: str | None = None,
        resources: FrozenSet[str] = frozenset(),
        network_scope: FrozenSet[str] = frozenset(),
        verifier: str | None = None,
        execute: Callable[[], object] | None = None,
    ) -> tuple[Decision, object | None]:
        if self.identity is None or not self.identity.valid_for(actor, self.manifest.manifest_id, self.manifest.environment):
            return self._deny(actor, action, 'invalid_execution_identity')
        if action not in self.manifest.allowed_actions:
            return self._deny(actor, action, 'manifest_action_not_allowed')
        if not capabilities.issubset(self.manifest.allowed_capabilities):
            return self._deny(actor, action, 'manifest_capability_not_allowed')
        if not self.containment.allow_capabilities(capabilities):
            return self._deny(actor, action, 'containment_capability_denied')
        if not self.containment.allow_network(network_scope):
            return self._deny(actor, action, 'containment_network_denied')
        if not self.containment.allow_filesystem(resources):
            return self._deny(actor, action, 'containment_filesystem_denied')

        request = OperationRequest(
            request_id=f'manifest:{self.manifest.manifest_id}',
            actor=actor,
            action=action,
            purpose=purpose,
            requested_capabilities=capabilities,
            resources=resources,
            network_scope=network_scope,
        )
        decision = self.runtime.decide(request, authorization_id, lease_id, verifier)
        if decision.decision != Decision.ALLOW:
            return decision.decision, None
        return Decision.ALLOW, execute() if execute else None

    def run_command(
        self,
        actor: str,
        command: list[str],
        authorization_id: str,
        lease_id: str,
        verifier: str | None = None,
    ) -> tuple[Decision, object | None]:
        decision, _ = self.request(
            actor,
            'build',
            'sandboxed command execution',
            frozenset({'build'}),
            authorization_id,
            lease_id,
            resources=frozenset({'/workspace'}),
            verifier=verifier,
        )
        if decision != Decision.ALLOW:
            return decision, None
        if self.sandbox is None:
            return Decision.DENY, SandboxUnavailable('sandbox runner not configured')
        try:
            result = self.sandbox.run(command)
        except (SandboxUnavailable, TimeoutError) as exc:
            return Decision.DENY, exc
        return Decision.ALLOW, result
