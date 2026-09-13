from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, FrozenSet

from .containment import ContainmentEnforcer
from .identity import ExecutionIdentity
from .models import Decision, OperationRequest
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
            return Decision.DENY, None
        if action not in self.manifest.allowed_actions:
            return Decision.DENY, None
        if not capabilities.issubset(self.manifest.allowed_capabilities):
            return Decision.DENY, None
        if not self.containment.allow_capabilities(capabilities):
            return Decision.DENY, None
        if not self.containment.allow_network(network_scope):
            return Decision.DENY, None
        if not self.containment.allow_filesystem(resources):
            return Decision.DENY, None
        request = OperationRequest(
            request_id=f'manifest:{self.manifest.manifest_id}', actor=actor, action=action,
            purpose=purpose, requested_capabilities=capabilities, resources=resources,
            network_scope=network_scope,
        )
        decision = self.runtime.decide(request, authorization_id, lease_id, verifier)
        if decision.decision != Decision.ALLOW:
            return decision.decision, None
        return Decision.ALLOW, execute() if execute else None

    def run_command(self, actor: str, command: list[str], authorization_id: str, lease_id: str,
                    verifier: str | None = None) -> tuple[Decision, object | None]:
        decision, _ = self.request(actor, 'build', 'sandboxed command execution', frozenset({'build'}),
                                   authorization_id, lease_id, resources=frozenset({'/workspace'}),
                                   verifier=verifier)
        if decision != Decision.ALLOW:
            return decision, None
        if self.sandbox is None:
            return Decision.DENY, SandboxUnavailable('sandbox runner not configured')
        try:
            result = self.sandbox.run(command)
        except (SandboxUnavailable, TimeoutError) as exc:
            return Decision.DENY, exc
        return Decision.ALLOW, result
