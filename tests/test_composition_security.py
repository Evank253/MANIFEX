from __future__ import annotations

from datetime import timedelta

from manifex_core.containment import Boundary, ContainmentEnforcer
from manifex_core.manifest import LLMManifest, ManifestExecutor
from manifex_core.models import Authorization, CapabilityLease, Decision, OperationRequest, now
from manifex_core.runtime import ManifexRuntime


def make_executor() -> ManifestExecutor:
    runtime = ManifexRuntime()
    auth = Authorization(
        id='auth-1', subject='llm-1', issuer='HUMAN', human_authority='human-1',
        action='build', purpose='authorized build', capabilities=frozenset({'build'}),
        resources=frozenset({'/workspace'}), network_scope=frozenset(),
        issued_at=now(), expires_at=now() + timedelta(minutes=5), approval='human-approval',
    )
    runtime.register_authorization(auth)
    runtime.issue_lease('auth-1', CapabilityLease(
        id='lease-1', authorization_id='auth-1', subject='llm-1',
        capabilities=frozenset({'build'}), issued_at=now(), expires_at=now() + timedelta(minutes=5),
    ))
    return ManifestExecutor(
        runtime=runtime,
        manifest=LLMManifest('manifest-1', 'test-llm', '1', frozenset({'build'}), frozenset({'build'})),
        containment=ContainmentEnforcer(Boundary(filesystem=frozenset({'/workspace'}), network=frozenset())),
    )


def test_direct_forbidden_attempt_is_blocked_without_execution():
    ex = make_executor()
    called = []
    decision, result = ex.request('llm-1', 'build', 'host escape', frozenset({'host_escape'}), 'auth-1', 'lease-1', execute=lambda: called.append(1))
    assert decision == Decision.DENY
    assert result is None
    assert not called


def test_proxy_capability_is_not_transitive():
    ex = make_executor()
    decision, _ = ex.request('llm-1', 'build', 'proxy attempt', frozenset({'build', 'unauthorized_network'}), 'auth-1', 'lease-1')
    assert decision == Decision.DENY


def test_unauthorized_network_is_denied_even_with_valid_build_lease():
    ex = make_executor()
    decision, _ = ex.request('llm-1', 'build', 'egress attempt', frozenset({'build'}), 'auth-1', 'lease-1', network_scope=frozenset({'internet'}))
    assert decision == Decision.DENY


def test_unauthorized_filesystem_is_denied():
    ex = make_executor()
    decision, _ = ex.request('llm-1', 'build', 'host filesystem attempt', frozenset({'build'}), 'auth-1', 'lease-1', resources=frozenset({'/etc'}))
    assert decision == Decision.DENY


def test_isolation_blocks_after_manifest_is_constructed():
    ex = make_executor()
    ex.containment.isolate()
    decision, _ = ex.request('llm-1', 'build', 'normal request', frozenset({'build'}), 'auth-1', 'lease-1')
    assert decision == Decision.DENY


def test_denial_is_audited():
    ex = make_executor()
    ex.request('llm-1', 'modify_constitution', 'takeover', frozenset(), 'auth-1', 'lease-1')
    assert ex.runtime.audit.events
    assert ex.runtime.audit.events[-1].result == 'BLOCKED'


def test_core_cannot_be_used_as_proxy_to_grant_authority():
    runtime = ManifexRuntime()
    request = OperationRequest('proxy-1', 'llm-1', 'modify_safety_kernel', 'proxy', frozenset())
    result = runtime.decide(request)
    assert result.decision == Decision.DENY


def test_expired_lease_removes_execution_authority():
    ex = make_executor()
    old = now() - timedelta(minutes=2)
    ex.runtime.leases['lease-1'] = CapabilityLease('lease-1', 'auth-1', 'llm-1', frozenset({'build'}), old, old + timedelta(seconds=1))
    decision, _ = ex.request('llm-1', 'build', 'expired', frozenset({'build'}), 'auth-1', 'lease-1')
    assert decision == Decision.DENY


if __name__ == '__main__':
    tests = [v for k, v in globals().items() if k.startswith('test_')]
    for test in tests:
        test()
    print(f'PASS {len(tests)} composition security tests')
