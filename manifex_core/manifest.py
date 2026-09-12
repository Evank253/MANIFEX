from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, FrozenSet

from .containment import ContainmentEnforcer
from .models import Decision, OperationRequest
from .runtime import ManifexRuntime


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
    """Routes LLM requests through Core before any supplied executor runs."""

    runtime: ManifexRuntime
    manifest: LLMManifest
    containment: ContainmentEnforcer = field(default_factory=ContainmentEnforcer)

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
