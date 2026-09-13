from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet


FORBIDDEN_CAPABILITIES = frozenset({
    "modify_constitution",
    "modify_safety_kernel",
    "disable_audit",
    "disable_shutdown",
    "forge_human_approval",
    "self_authorize",
    "self_replicate",
    "unauthorized_persistence",
    "unauthorized_network",
    "credential_root_access",
    "host_escape",
})


@dataclass(frozen=True)
class Boundary:
    filesystem: FrozenSet[str] = frozenset()
    network: FrozenSet[str] = frozenset()
    credentials: FrozenSet[str] = frozenset()
    processes: FrozenSet[str] = frozenset()
    resources: FrozenSet[str] = frozenset()
    environment: str = "sandbox"


@dataclass
class ContainmentEnforcer:
    """Deny-by-default policy layer for MANIFEX-controlled execution.

    This is an enforcement contract, not a claim that OS/container isolation is
    already physically installed. Deployment adapters must bind these decisions
    to real sandbox, firewall, credential, and process controls.
    """

    boundary: Boundary = field(default_factory=Boundary)
    isolated: bool = False
    terminated: bool = False

    def allow_capabilities(self, requested: FrozenSet[str]) -> bool:
        if self.isolated or self.terminated:
            return False
        return not requested.intersection(FORBIDDEN_CAPABILITIES)

    def allow_network(self, destinations: FrozenSet[str]) -> bool:
        if self.isolated or self.terminated:
            return False
        return destinations.issubset(self.boundary.network)

    def allow_filesystem(self, paths: FrozenSet[str]) -> bool:
        if self.isolated or self.terminated:
            return False
        return paths.issubset(self.boundary.filesystem)

    def allow_credentials(self, names: FrozenSet[str]) -> bool:
        if self.isolated or self.terminated:
            return False
        return names.issubset(self.boundary.credentials)

    def isolate(self) -> None:
        self.isolated = True

    def terminate(self) -> None:
        self.terminated = True
        self.isolated = True

    def status(self) -> dict[str, object]:
        return {
            "isolated": self.isolated,
            "terminated": self.terminated,
            "environment": self.boundary.environment,
        }
