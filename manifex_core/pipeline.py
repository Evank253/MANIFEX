"""MANIFEX discovery-to-index orchestration without automatic acquisition."""
from __future__ import annotations
import time
from typing import Iterable
from .build_index import Asset, BuildIndex
from .discovery import AssetDiscoveryEngine, RepositoryInspection
from .evaluator import CandidateEvaluator, CandidateScore

class DiscoveryPipeline:
    def __init__(self, discovery: AssetDiscoveryEngine, index: BuildIndex | None = None):
        self.discovery = discovery; self.index = index or BuildIndex(); self.evaluator = CandidateEvaluator()

    def inspect_and_register(self, query: str, limit: int = 20) -> list[Asset]:
        assets = []
        for candidate in self.discovery.discover(query, limit):
            inspection = self.discovery.inspect_candidate(candidate)
            asset_id = self.index.make_id(inspection.repository, inspection.revision, "repository")
            if self.index.get(asset_id): continue
            repo_meta = self.discovery.provider.repository(inspection.repository)
            branch = str(repo_meta.get("default_branch") or "")
            discovery_id = self.index.make_discovery_id("github", query, inspection.repository, inspection.revision)
            source_url = f"https://github.com/{inspection.repository}"
            asset = Asset(
                asset_id=asset_id, name=inspection.repository, source_repository=inspection.repository,
                source_branch=branch, source_commit=inspection.revision, tree_hash=inspection.tree_hash,
                asset_path="repository", source_license=inspection.license_name, asset_type="TOOL",
                dependencies=list(inspection.manifests), capabilities=list(inspection.capabilities),
                interfaces=list(inspection.interfaces), tests=list(inspection.test_paths),
                runtime_status="INDICATED" if inspection.runtime_indicators else "NOT_MEASURED",
                evidence_level="NOT_MEASURED", manifex_action="ADAPT",
                provenance={"source_url":source_url, "discovery_provider":"github", "immutable_revision":True},
                discovery={"discovery_id":discovery_id, "provider":"github", "method":"repository_search",
                           "query":query, "timestamp":time.time(), "context":"MANIFEX discovery pipeline",
                           "source_url":source_url, "source_repository":inspection.repository,
                           "source_branch":branch, "source_commit":inspection.revision, "source_tree_hash":inspection.tree_hash},
                engineering={"action":"ADAPT"}, evidence={"hints":list(inspection.evidence_hints)},
                lineage={"discovered_from":discovery_id}, notes="Discovered/inspected candidate; not verified.",
            )
            self.index.add(asset); assets.append(asset)
        return assets

    def rank(self, inspections: Iterable[RepositoryInspection], required_capabilities: Iterable[str]) -> list[CandidateScore]:
        return self.evaluator.rank(self.evaluator.evaluate(i, required_capabilities) for i in inspections)
