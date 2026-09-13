"""Requirement decomposition and capability coverage for MANIFEX."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .build_index import Asset

STATUSES = ("HAVE", "PARTIAL", "MISSING", "UNKNOWN", "CONFLICTING", "UNVERIFIED")


@dataclass(frozen=True)
class CapabilityRequirement:
    name: str
    description: str = ""
    required: bool = True
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class Coverage:
    capability: str
    status: str
    asset_ids: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    rationale: str = ""


@dataclass(frozen=True)
class GapReport:
    requirement: str
    capabilities: tuple[CapabilityRequirement, ...]
    coverage: tuple[Coverage, ...]

    @property
    def gaps(self) -> tuple[Coverage, ...]:
        return tuple(x for x in self.coverage if x.status != "HAVE")


class GapEngine:
    """Maps requirements to indexed capabilities without claiming missing proof."""

    def analyze(self, requirement: str, capabilities: Iterable[CapabilityRequirement], assets: Iterable[Asset]) -> GapReport:
        assets = tuple(assets)
        rows = []
        for cap in capabilities:
            keyset = {cap.name.lower(), *(x.lower() for x in cap.aliases)}
            matches = tuple(a for a in assets if keyset.intersection(x.lower() for x in a.capabilities))
            ids = tuple(a.asset_id for a in matches)
            if not matches:
                status = "MISSING"
                rationale = "No indexed capability match."
            elif any(a.verification_status == "FAILED" for a in matches):
                status = "CONFLICTING"
                rationale = "At least one matching asset has failed verification."
            elif any(a.state in {"VERIFIED", "REUSABLE"} for a in matches):
                status = "HAVE"
                rationale = "A matching asset has reached executable verification."
            elif any(a.evidence_level != "NOT_MEASURED" for a in matches):
                status = "PARTIAL"
                rationale = "A candidate exists, but reusable verification is not established."
            else:
                status = "UNVERIFIED"
                rationale = "A candidate exists without measured evidence."
            rows.append(Coverage(cap.name, status, ids, tuple(sorted({a.evidence_level for a in matches})), rationale))
        return GapReport(requirement, tuple(capabilities), tuple(rows))
