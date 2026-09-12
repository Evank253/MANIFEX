from datetime import timedelta

from manifex_core.containment import Boundary, ContainmentEnforcer
from manifex_core.gate import EngineeringGate, GateStatus, REQUIRED_GATES
from manifex_core.manifest import LLMManifest, ManifestExecutor
from manifex_core.models import Authorization, CapabilityLease, Decision, now
from manifex_core.runtime import ManifexRuntime


def test_forbidden_capability_is_denied():
    e = ContainmentEnforcer(Boundary())
    assert not e.allow_capabilities(frozenset({'host_escape'}))


def test_isolation_removes_capability():
    e = ContainmentEnforcer(Boundary(network=frozenset({'example.test'})))
    e.isolate()
    assert not e.allow_network(frozenset({'example.test'}))


def test_termination_is_terminal_for_enforcer():
    e = ContainmentEnforcer(Boundary())
    e.terminate()
    assert e.terminated and e.isolated
    assert not e.allow_capabilities(frozenset({'build'}))


def test_gate_missing_evidence_is_blocked():
    gate = EngineeringGate()
    assert gate.finalize() == GateStatus.BLOCKED


def test_gate_requires_every_stage():
    gate = EngineeringGate()
    gate.start()
    for name in REQUIRED_GATES:
        gate.record(name, True)
    assert gate.finalize() == GateStatus.VERIFIED


def test_gate_failure_cannot_become_verified():
    gate = EngineeringGate()
    gate.start()
    for name in REQUIRED_GATES:
        gate.record(name, True)
    gate.record('security_tests', False)
    assert gate.finalize() == GateStatus.FAILED


def test_manifest_denies_action_outside_manifest():
    executor = ManifestExecutor(
        ManifexRuntime(),
        LLMManifest('m1', 'llm', '1', allowed_actions=frozenset({'build'}), allowed_capabilities=frozenset({'build'})),
    )
    decision, result = executor.request('agent-1', 'deploy', 'test', frozenset({'build'}), execute=lambda: 'executed')
    assert decision == Decision.DENY and result is None


def test_manifest_requires_authorized_lease():
    runtime = ManifexRuntime()
    t = now()
    auth = Authorization(
        id='auth-manifest', subject='agent-1', issuer='HUMAN', human_authority='human-1',
        action='build', purpose='manifest-test', capabilities=frozenset({'build'}),
        issued_at=t - timedelta(seconds=1), expires_at=t + timedelta(seconds=60),
        approval='human-signature',
    )
    runtime.register_authorization(auth)
    lease = CapabilityLease('lease-manifest', 'auth-manifest', 'agent-1', frozenset({'build'}), auth.issued_at, auth.expires_at)
    runtime.issue_lease('auth-manifest', lease)
    executor = ManifestExecutor(
        runtime,
        LLMManifest('m2', 'llm', '1', allowed_actions=frozenset({'build'}), allowed_capabilities=frozenset({'build'})),
    )
    decision, result = executor.request(
        'agent-1', 'build', 'manifest-test', frozenset({'build'}),
        authorization_id='auth-manifest', lease_id='lease-manifest', verifier='verifier',
        execute=lambda: 'executed',
    )
    assert decision == Decision.ALLOW and result == 'executed'


def test_manifest_never_executes_after_containment_failure():
    containment = ContainmentEnforcer()
    containment.terminate()
    executor = ManifestExecutor(
        ManifexRuntime(),
        LLMManifest('m3', 'llm', '1', allowed_actions=frozenset({'build'}), allowed_capabilities=frozenset({'build'})),
        containment=containment,
    )
    decision, result = executor.request('agent-1', 'build', 'test', frozenset({'build'}), execute=lambda: 'must-not-run')
    assert decision == Decision.DENY and result is None


if __name__ == '__main__':
    tests = [value for name, value in globals().items() if name.startswith('test_')]
    for test in tests:
        test()
    print(f'PASS {len(tests)} containment tests')
