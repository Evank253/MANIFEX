from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


class GateStatus(str, Enum):
    DRAFT = "DRAFT"
    TESTING = "TESTING"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    VERIFIED = "VERIFIED"


REQUIRED_GATES = (
    "build",
    "type_check",
    "lint",
    "unit_tests",
    "integration_tests",
    "e2e_tests",
    "security_tests",
    "constitutional_tests",
    "deployment_rehearsal",
    "failure_injection",
    "performance",
    "provenance",
    "audit",
    "independent_verification",
)


@dataclass
class EngineeringGate:
    """Evidence gate. A missing required result can never become VERIFIED."""

    results: dict[str, bool | None] = field(default_factory=dict)
    status: GateStatus = GateStatus.DRAFT

    def start(self) -> None:
        self.status = GateStatus.TESTING

    def record(self, name: str, passed: bool | None) -> None:
        if name not in REQUIRED_GATES:
            raise KeyError(f"unknown gate: {name}")
        self.results[name] = passed
        if passed is False:
            self.status = GateStatus.FAILED
        elif self.status != GateStatus.FAILED:
            self.status = GateStatus.TESTING

    def finalize(self) -> GateStatus:
        if any(self.results.get(name) is False for name in REQUIRED_GATES):
            self.status = GateStatus.FAILED
        elif any(self.results.get(name) is not True for name in REQUIRED_GATES):
            self.status = GateStatus.BLOCKED
        else:
            self.status = GateStatus.VERIFIED
        return self.status

    def run(self, checks: dict[str, Callable[[], bool]]) -> GateStatus:
        self.start()
        for name in REQUIRED_GATES:
            check = checks.get(name)
            if check is None:
                self.record(name, None)
                continue
            try:
                self.record(name, bool(check()))
            except Exception:
                self.record(name, False)
        return self.finalize()

    @property
    def verified(self) -> bool:
        return self.finalize() == GateStatus.VERIFIED
