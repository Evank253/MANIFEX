"""Requirement decomposition and generalized engineering gap classification."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Iterable
from .build_index import Asset

STATUSES = ("HAVE", "PARTIAL", "MISSING", "UNKNOWN", "CONFLICTING", "UNVERIFIED")

class GapType(str, Enum):
    TOOL_GAP="TOOL_GAP"; ENGINE_GAP="ENGINE_GAP"; INTERFACE_GAP="INTERFACE_GAP"; RUNTIME_GAP="RUNTIME_GAP"; DEPENDENCY_GAP="DEPENDENCY_GAP"; DATA_GAP="DATA_GAP"; MODEL_GAP="MODEL_GAP"; INFRASTRUCTURE_GAP="INFRASTRUCTURE_GAP"; SECURITY_GAP="SECURITY_GAP"; TESTING_GAP="TESTING_GAP"; OBSERVABILITY_GAP="OBSERVABILITY_GAP"; GOVERNANCE_GAP="GOVERNANCE_GAP"; DEPLOYMENT_GAP="DEPLOYMENT_GAP"; UNKNOWN_GAP="UNKNOWN_GAP"

@dataclass(frozen=True)
class CapabilityRequirement:
    name: str; description: str=""; required: bool=True; aliases: tuple[str,...]=()

@dataclass(frozen=True)
class Coverage:
    capability: str; status: str; asset_ids: tuple[str,...]=(); evidence: tuple[str,...]=(); rationale: str=""; gap_type: GapType|None=None

@dataclass(frozen=True)
class Gap:
    gap_id: str; requirement: str; capability: str; gap_type: GapType; evidence: tuple[str,...]=(); candidate_asset_ids: tuple[str,...]=(); rationale: str=""; build_authorized: bool=False; target_asset_id: str=""

@dataclass(frozen=True)
class GapReport:
    requirement: str; capabilities: tuple[CapabilityRequirement,...]; coverage: tuple[Coverage,...]; gaps: tuple[Gap,...]=()

class GapEngine:
    """Diagnoses missing layers. Classification never authorizes construction."""
    def _id(self, *parts: str) -> str:
        import hashlib
        return "gap-" + hashlib.sha256("|".join(parts).encode()).hexdigest()[:20]

    def analyze(self, requirement: str, capabilities: Iterable[CapabilityRequirement], assets: Iterable[Asset]) -> GapReport:
        assets=tuple(assets); rows=[]; gaps=[]
        for cap in capabilities:
            keys={cap.name.lower(), *(x.lower() for x in cap.aliases)}; matches=tuple(a for a in assets if keys.intersection(x.lower() for x in a.capabilities)); ids=tuple(a.asset_id for a in matches)
            if not matches: status,rationale,gt="MISSING","No indexed capability match.",GapType.TOOL_GAP
            elif any(a.verification_status=="FAILED" for a in matches): status,rationale,gt="CONFLICTING","At least one matching asset has failed verification.",GapType.UNKNOWN_GAP
            elif any(a.state in {"VERIFIED","REUSABLE"} for a in matches): status,rationale,gt="HAVE","A matching asset has reached executable verification.",None
            elif any(a.evidence_level!="NOT_MEASURED" for a in matches): status,rationale,gt="PARTIAL","A candidate exists, but reusable verification is not established.",GapType.TESTING_GAP
            else: status,rationale,gt="UNVERIFIED","A candidate exists without measured evidence.",GapType.TESTING_GAP
            rows.append(Coverage(cap.name,status,ids,tuple(sorted({a.evidence_level for a in matches})),rationale,gt))
            if gt: gaps.append(Gap(self._id(requirement,cap.name,gt.value),requirement,cap.name,gt,tuple(sorted({a.evidence_level for a in matches})),ids,rationale,False))
        return GapReport(requirement,tuple(capabilities),tuple(rows),tuple(gaps))

    def classify_engine_gap(self, requirement: str, capability: str, target_asset: Asset, available_engines: Iterable[Asset], required_engine: str) -> Gap:
        """Creates an ENGINE_GAP when a usable target tool requires an absent/inadequate engine."""
        engines=tuple(available_engines); key=required_engine.lower()
        adequate=tuple(e for e in engines if key in {x.lower() for x in e.capabilities} and e.verification_status in {"VERIFIED","QUALIFIED"} and e.evidence_level != "NOT_MEASURED")
        rationale = "No verified engine satisfies the target tool's required engine." if not adequate else "A verified compatible engine exists."
        return Gap(self._id(requirement,capability,target_asset.asset_id,required_engine,GapType.ENGINE_GAP.value),requirement,capability,GapType.ENGINE_GAP,tuple(e.evidence_level for e in engines),tuple(e.asset_id for e in engines),rationale,False,target_asset.asset_id)
