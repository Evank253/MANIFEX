"""MANIFEX discovery-to-index orchestration without automatic acquisition."""
from __future__ import annotations

from typing import Iterable

from .build_index import Asset, BuildIndex
from .discovery import AssetDiscoveryEngine, RepositoryInspection
from .evaluator import CandidateEvaluator, CandidateScore


class DiscoveryPipeline:
    def __init__(self, discovery: AssetDiscoveryEngine, index: BuildIndex | None = None):
        self.discovery = discovery
        self.index = index or BuildIndex()
        self.evaluator = CandidateEvaluator()

    def inspect_and_register(self, query: str, limit: int = 20) -> list[Asset]:
        assets = []
        for candidate in self.discovery.discover(query, limit):
            inspection = self.discovery.inspect_candidate(candidate)
            asset_id = self.index.make_id(inspection.repository, inspection.revision, "repository")
            if self.index.get(asset_id):
                continue
            asset = Asset(
                asset_id=asset_id,
                name=inspection.repository,
                source_repository=inspection.repository,
                source_branch=inspection.revision,
                source_commit=inspection.revision,
                tree_hash=inspection.tree_hash,
                source_license=inspection.license_name,
                dependencies=list(inspection.manifests),
                capabilities=list(inspection.capabilities),
                interfaces=list(inspection.interfaces),
                tests=list(inspection.test_paths),
                runtime_status="INDICATED" if inspection.runtime_indicators else "NOT_MEASURED",
                evidence_level="NOT_MEASURED",
                manifex_action="ADAPT",
                provenance={"discovery": "github", "heuristic_classification": True},
                notes="Discovered/inspected candidate; not verified.",
            )
            self.index.add(asset)
            assets.append(asset)
        return assets

    def rank(self, inspections: Iterable[RepositoryInspection], required_capabilities: Iterable[str]) -> list[CandidateScore]:
        return self.evaluator.rank(self.evaluator.evaluate(i, required_capabilities) for i in inspections)
