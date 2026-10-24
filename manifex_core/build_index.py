"""MANIFEX Build Index: authoritative asset registry with lineage."""
from __future__ import annotations
import hashlib, json, time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

STATES = ("DISCOVERED", "INSPECTED", "QUALIFIED", "APPROVED", "IMPORTED", "VERIFIED", "REUSABLE")
ACTIONS = ("KEEP", "ADAPT", "WRAP", "FREEZE", "BUILD", "REPLACE", "RETIRE")
EVIDENCE = {"E0", "E1", "E2", "E3", "E4", "E5", "NOT_MEASURED"}
TRANSITIONS = {a: b for a, b in zip(STATES, STATES[1:])}

@dataclass
class Asset:
    asset_id: str
    name: str
    source_repository: str
    source_branch: str = ""
    source_commit: str = ""
    tree_hash: str = ""
    asset_path: str = ""
    source_license: str = "NOT_MEASURED"
    asset_type: str = "ASSET"
    dependencies: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    interfaces: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    runtime_status: str = "NOT_MEASURED"
    evidence_level: str = "NOT_MEASURED"
    manifex_action: str = "ADAPT"
    provenance: dict[str, Any] = field(default_factory=dict)
    copy_id: str = ""
    working_copy: str = ""
    modifications: list[str] = field(default_factory=list)
    state: str = "DISCOVERED"
    verification_status: str = "NOT_MEASURED"
    qualification_status: str = "BLOCKED"
    promotion_status: str = "BLOCKED"
    discovery: dict[str, Any] = field(default_factory=dict)
    acquisition: dict[str, Any] = field(default_factory=dict)
    engineering: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    lineage: dict[str, Any] = field(default_factory=dict)
    originating_requirement: str = ""
    originating_gap_id: str = ""
    originating_project: str = ""
    supports: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    derived_from: list[str] = field(default_factory=list)
    supersedes: list[str] = field(default_factory=list)
    reused_by: list[str] = field(default_factory=list)
    notes: str = ""
    updated_at: float = field(default_factory=time.time)

class BuildIndex:
    """Append-only JSONL registry. Original source repositories remain untouched."""
    def __init__(self, root: str | Path = ".manifex"):
        self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True)
        self.index = self.root / "build_index.jsonl"; self.ledger = self.root / "build_index_ledger.jsonl"

    @staticmethod
    def make_id(repo: str, commit: str, path: str) -> str:
        return "asset-" + hashlib.sha256(f"{repo}|{commit}|{path}".encode()).hexdigest()[:20]

    @staticmethod
    def make_discovery_id(provider: str, query: str, repo: str, commit: str) -> str:
        return "discovery-" + hashlib.sha256(f"{provider}|{query}|{repo}|{commit}".encode()).hexdigest()[:20]

    def _records(self) -> dict[str, Asset]:
        out = {}
        if self.index.exists():
            for line in self.index.read_text().splitlines():
                if line.strip():
                    a = Asset(**json.loads(line)); out[a.asset_id] = a
        return out

    def _append(self, path: Path, value: dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8") as f: f.write(json.dumps(value, sort_keys=True) + "\n")

    def add(self, asset: Asset) -> Asset:
        if asset.state not in STATES or asset.manifex_action not in ACTIONS or asset.evidence_level not in EVIDENCE:
            raise ValueError("invalid asset state, action, or evidence level")
        if asset.asset_id in self._records(): raise ValueError(f"asset already indexed: {asset.asset_id}")
        self._append(self.index, asdict(asset))
        self._append(self.ledger, {"event":"ASSET_DISCOVERED", "asset_id":asset.asset_id,
                                   "source_repository":asset.source_repository, "source_commit":asset.source_commit,
                                   "discovery_id":asset.discovery.get("discovery_id", ""), "state":asset.state, "timestamp":time.time()})
        return asset

    def get(self, asset_id: str) -> Optional[Asset]: return self._records().get(asset_id)

    def transition(self, asset_id: str, new_state: str, *, evidence_level: Optional[str]=None,
                   verification_status: Optional[str]=None, notes: Optional[str]=None) -> Asset:
        old = self.get(asset_id)
        if not old: raise KeyError(asset_id)
        if new_state not in STATES or TRANSITIONS.get(old.state) != new_state: raise ValueError(f"invalid transition: {old.state} -> {new_state}")
        if evidence_level is not None and evidence_level not in EVIDENCE: raise ValueError("invalid evidence level")
        data = asdict(old); data["state"] = new_state; data["updated_at"] = time.time()
        if evidence_level is not None: data["evidence_level"] = evidence_level
        if verification_status is not None: data["verification_status"] = verification_status
        if notes is not None: data["notes"] = notes
        new = Asset(**data); self._append(self.index, data)
        self._append(self.ledger, {"event":"STATE_TRANSITION", "asset_id":asset_id, "from":old.state, "to":new_state,
                                   "evidence_level":new.evidence_level, "timestamp":time.time()})
        return new

    def search(self, query: str = "", state: Optional[str]=None, action: Optional[str]=None) -> list[Asset]:
        q = query.lower(); rows = list(self._records().values())
        return sorted([a for a in rows if (not state or a.state == state) and (not action or a.manifex_action == action)
                       and (not q or q in json.dumps(asdict(a)).lower())], key=lambda a: a.name.lower())

    def _where(self, fn) -> list[Asset]: return sorted([a for a in self._records().values() if fn(a)], key=lambda a: a.name.lower())
    def find_by_capability(self, capability: str) -> list[Asset]: return self._where(lambda a: capability.lower() in {x.lower() for x in a.capabilities})
    def find_by_requirement(self, requirement: str) -> list[Asset]: return self._where(lambda a: a.originating_requirement.lower() == requirement.lower())
    def find_by_gap(self, gap_id: str) -> list[Asset]: return self._where(lambda a: a.originating_gap_id == gap_id or a.engineering.get("engine_gap_id") == gap_id)
    def find_by_engine(self, engine_id: str) -> list[Asset]: return self._where(lambda a: a.engineering.get("engine_id") == engine_id or engine_id in a.depends_on)
    def find_tools_supported_by_engine(self, engine_id: str) -> list[Asset]: return self._where(lambda a: a.asset_type == "TOOL" and engine_id in a.depends_on)
    def find_assets_supporting_requirement(self, requirement: str) -> list[Asset]: return self._where(lambda a: requirement.lower() in {x.lower() for x in a.supports})
    def find_originating_project(self, project: str) -> list[Asset]: return self._where(lambda a: a.originating_project == project)
    def find_discovery_source(self, source: str) -> list[Asset]: return self._where(lambda a: source.lower() in json.dumps(a.discovery, sort_keys=True).lower() or source.lower() in a.source_repository.lower())
    def find_dependents(self, asset_id: str) -> list[Asset]: return self._where(lambda a: asset_id in a.depends_on)
    def find_reused_by(self, project: str) -> list[Asset]: return self._where(lambda a: project in a.reused_by)

    def trace_forward(self, asset_id: str) -> dict[str, Any]:
        asset = self.get(asset_id)
        if not asset: raise KeyError(asset_id)
        return {"asset": asset, "dependents": self.find_dependents(asset_id), "reused_by": list(asset.reused_by), "supports": list(asset.supports), "supersedes": list(asset.supersedes)}

    def trace_backward(self, asset_id: str) -> dict[str, Any]:
        asset = self.get(asset_id)
        if not asset: raise KeyError(asset_id)
        return {"asset": asset, "derived_from": [self.get(x) for x in asset.derived_from if self.get(x)],
                "dependencies": [self.get(x) for x in asset.depends_on if self.get(x)], "discovery": dict(asset.discovery),
                "originating_gap_id": asset.originating_gap_id, "originating_requirement": asset.originating_requirement,
                "originating_project": asset.originating_project}

    def summary(self) -> dict[str, Any]:
        rows = list(self._records().values())
        return {"asset_count":len(rows), "by_state":{s:sum(a.state==s for a in rows) for s in STATES},
                "by_action":{x:sum(a.manifex_action==x for a in rows) for x in ACTIONS},
                "by_type":{t:sum(a.asset_type==t for a in rows) for t in sorted({a.asset_type for a in rows})}}
