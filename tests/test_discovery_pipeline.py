from manifex_core.discovery import RepositoryInspector
from manifex_core.gap import CapabilityRequirement, GapEngine
from manifex_core.evaluator import CandidateEvaluator
from manifex_core.acquisition import AcquisitionEngine
from manifex_core.qualification import QualificationEngine
from manifex_core.verification import VerificationEngine


def test_inspector_marks_heuristics_as_hints():
    repo = {"full_name": "example/tool", "default_branch": "main", "stargazers_count": 100}
    tree = [{"path": "README.md", "type": "blob"}, {"path": "pyproject.toml", "type": "blob"}, {"path": "tests/test_api.py", "type": "blob"}, {"path": "security/auth.py", "type": "blob"}]
    result = RepositoryInspector().inspect(repo, tree)
    assert "security" in result.capabilities
    assert "tests-present" in result.evidence_hints
    assert result.license_name == "NOT_MEASURED"


def test_gap_does_not_treat_discovery_as_have():
    report = GapEngine().analyze("security", [CapabilityRequirement("security")], [])
    assert report.coverage[0].status == "MISSING"


def test_acquisition_requires_immutable_revision():
    try:
        AcquisitionEngine.make_plan("example/tool", "", "tree", "MANIFEX/tool")
    except ValueError:
        return
    raise AssertionError("acquisition accepted missing source revision")


def test_verification_requires_all_supplied_gates():
    result = VerificationEngine().evaluate({"tests": True, "security": False}, evidence_level="E2")
    assert result.status == "FAILED"
    assert not result.passed


def test_qualification_requires_verification_and_license():
    q = QualificationEngine().decide(state="VERIFIED", evidence_level="E2", verification_status="VERIFIED", license_known=False, tests_passed=True)
    assert not q.approved
    q = QualificationEngine().decide(state="VERIFIED", evidence_level="E2", verification_status="VERIFIED", license_known=True, tests_passed=True)
    assert q.approved and q.state == "REUSABLE"
