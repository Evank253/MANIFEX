"""Requirement decomposition and generalized engineering gap classification."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Iterable
from .build_index import Asset

STATUSES = ("HAVE", "PARTIAL", "MISSING", "UNKNOWN", "CONFLICTING", "UNVERIFIED")

class GapType(str, Enum):
    TOOL_GAP = "TOOL_GAP"
    ENGINE_GAP = "ENGINE_GAP"
    INTERFACE_GAP = "INTERFACE_GAP"
    RUNTIME_GAP = "RUNTIME_GAP"
    DEPENDENCY_GAP = "DEPENDENCY_GAP"
    DATA_GAP = "DATA_GAP"
    MODEL_GAP = "MODEL_GAP"
    INFRASTRUCTURE_GAP = "INFRASTRUCTURE_GAP"
    SECURITY_GAP = "SECURITY_GAP"
    TESTING_GAP = "TESTING_GAP"
    OBSERVABILITY_GAP = "OBSERVABILITY_GAP"
    GOVERNANCE_GAP = "GOVERNANCE_GAP"
    DEPLOYMENT_GAP = "DEPLOYMENT_GAP"
    UNKNOWN_GAP = "UNKNOWN_GAP"

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
    gap_type: GapType | None = None

@dataclass(frozen=True)
class Gap:
    gap_id: str
    requirement: str
    capability: str
    gap_type: GapType
    evidence: tuple[str, ...] = ()
    candidate_asset_ids: tuple[str, ...] = ()
    rationale: str = ""
    build_authorized: bool = False

@dataclass(frozen=True)
class GapReport:
    requirement: str
    capabilities: tuple[CapabilityRequirement, ...]
    coverage: tuple[Coverage, ...]
    gaps: tuple[Gap, ...] = ()

class GapEngine:
    """Maps requirements to indexed capabilities and distinguishes gap layers.

    A gap classification never authorizes construction; build_authorized remains False
    until a separate evidence-bearing governance decision exists.
    """
    def analyze(self, requirement: str, capabilities: Iterable[CapabilityRequirement], assets: Iterable[Asset]) -> GapReport:
        assets = tuple(assets); rows = []; gaps = []
        for cap in capabilities:
            keyset = {cap.name.lower(), *(x.lower() for x in cap.aliases)}
            matches = tuple(a for a in assets if keyset.intersection(x.lower() for x in a.capabilities))
            ids = tuple(a.asset_id for a in matches)
            if not matches:
                status, rationale, gap_type = "MISSING", "No indexed capability match.", GapType.TOOL_GAP
            elif any(a.verification_status == "FAILED" for a in matches):
                status, rationale, gap_type = "CONFLICTING", "At least one matching asset has failed verification.", GapType.UNKNOWN_GAP
            elif any(a.state in {"VERIFIED", "REUSABLE"} for a in matches):
                status, rationale, gap_type = "HAVE", "A matching asset has reached executable verification.", None
            elif any(a.evidence_level != "NOT_MEASURED" for a in matches):
                status, rationale, gap_type = "PARTIAL", "A candidate exists, but reusable verification is not established.", GapType.VERIFICATION_GAP
            else:
                status, rationale, gap_type = "UNVERIFIED", "A candidate exists without measured evidence.", GapType.VERIFICATION_GAP
            rows.append(Coverage(cap.name, status, ids, tuple(sorted({a.evidence_level for a in matches})), rationale, gap_type))
            if gap_type is not None:
                import hashlib
                gid = "gap-" + hashlib.sha256(f"{requirement}|{cap.name}|{gap_type.value}".encode()).hexdigest()[:20]
                gaps.append(Gap(gid, requirement, cap.name, gap_type, tuple(sorted({a.evidence_level for a in matches})), ids, rationale, False))
        return GapReport(requirement, tuple(capabilities), tuple(rows), tuple(gaps))
