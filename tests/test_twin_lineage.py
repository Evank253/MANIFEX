"""Twin Sister gate for Build Index lineage and generalized gaps."""
from manifex_core.build_index import Asset, BuildIndex
from manifex_core.gap import CapabilityRequirement, GapEngine, GapType


def test_asset_preserves_discovery_and_engineering_lineage(tmp_path):
    index = BuildIndex(tmp_path / ".manifex")
    asset = Asset(
        "tool-1", "tool", "example/tool", source_branch="main", source_commit="a"*40, tree_hash="b"*40,
        asset_type="TOOL", capabilities=["security"],
        discovery={"provider":"github", "query":"security tool", "source_url":"https://github.com/example/tool"},
        originating_requirement="endpoint security", originating_gap_id="gap-1", originating_project="PROJECT-A",
        lineage={"discovered_from":"discovery-1", "created_from":"gap-1"})
    index.add(asset); got=index.get("tool-1")
    assert got.discovery["provider"] == "github"
    assert got.source_commit == "a"*40 and got.originating_gap_id == "gap-1"
    assert got.verification_status == "NOT_MEASURED" and got.qualification_status == "BLOCKED"


def test_tool_gap_does_not_authorize_build():
    gap = GapEngine().analyze("endpoint security", [CapabilityRequirement("endpoint")], []).gaps[0]
    assert gap.gap_type is GapType.TOOL_GAP and gap.build_authorized is False


def test_engine_gap_is_first_class_and_not_build_authorization():
    target = Asset("tool-1", "tool", "example/tool", asset_type="TOOL", capabilities=["security"])
    gap = GapEngine().classify_engine_gap("endpoint security", "security", target, [], "runtime-adapter")
    assert gap.gap_type is GapType.ENGINE_GAP
    assert gap.target_asset_id == "tool-1"
    assert gap.build_authorized is False


def test_lineage_queries(tmp_path):
    index = BuildIndex(tmp_path / ".manifex")
    engine = Asset("engine-1", "engine", "example/engine", asset_type="ENGINE", capabilities=["endpoint"], supports=["endpoint security"])
    tool = Asset("tool-1", "tool", "example/tool", asset_type="TOOL", capabilities=["endpoint"], depends_on=["engine-1"], originating_project="PROJECT-A", reused_by=["PROJECT-B"])
    index.add(engine); index.add(tool)
    assert index.find_by_capability("endpoint")[0].asset_id == "engine-1"
    assert index.find_tools_supported_by_engine("engine-1")[0].asset_id == "tool-1"
    assert index.find_reused_by("PROJECT-B")[0].asset_id == "tool-1"
    assert index.trace_backward("tool-1")["dependencies"][0].asset_id == "engine-1"
    assert index.trace_forward("engine-1")["dependents"][0].asset_id == "tool-1"


def test_unmeasured_asset_cannot_become_reusable_from_metadata(tmp_path):
    index = BuildIndex(tmp_path / ".manifex")
    asset = Asset("tool-2", "tool", "example/tool", asset_type="TOOL", capabilities=["security"])
    index.add(asset)
    assert (asset.state, asset.evidence_level, asset.verification_status, asset.qualification_status) == ("DISCOVERED", "NOT_MEASURED", "NOT_MEASURED", "BLOCKED")
