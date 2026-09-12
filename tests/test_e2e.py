from datetime import timedelta
from manifex_core.models import Authorization, CapabilityLease, OperationRequest, Decision, now
from manifex_core.runtime import ManifexRuntime


def make_auth(expired=False):
    t = now()
    return Authorization(id='a1', subject='agent-1', issuer='HUMAN', human_authority='human-1', action='build', purpose='test', capabilities=frozenset({'build'}), issued_at=t - timedelta(seconds=1), expires_at=t + timedelta(seconds=-1 if expired else 60), approval='human-signature')


def test_valid_authorization_allows():
    r = ManifexRuntime(); a = make_auth(); r.register_authorization(a)
    l = CapabilityLease('l1', 'a1', 'agent-1', frozenset({'build'}), a.issued_at, a.expires_at); r.issue_lease('a1', l)
    d = r.decide(OperationRequest('q1', 'agent-1', 'build', 'test', frozenset({'build'})), 'a1', 'l1', verifier='verifier')
    assert d.decision == Decision.ALLOW


def test_missing_authorization_denies():
    r = ManifexRuntime(); d = r.decide(OperationRequest('q2', 'agent-1', 'build', 'test', frozenset({'build'})))
    assert d.decision == Decision.DENY


def test_expired_authorization_denies():
    r = ManifexRuntime(); a = make_auth(True); r.register_authorization(a)
    try:
        r.issue_lease('a1', CapabilityLease('l2', 'a1', 'agent-1', frozenset({'build'}), a.issued_at, a.expires_at))
    except PermissionError:
        pass
    else:
        raise AssertionError('expired authorization issued a lease')


def test_constitution_modification_denies():
    r = ManifexRuntime(); d = r.decide(OperationRequest('q3', 'agent-1', 'modify_constitution', 'test', frozenset({'governance'})))
    assert d.decision == Decision.DENY


def test_self_verification_denies():
    r = ManifexRuntime(); a = make_auth(); r.register_authorization(a); l = CapabilityLease('l3', 'a1', 'agent-1', frozenset({'build'}), a.issued_at, a.expires_at); r.issue_lease('a1', l)
    d = r.decide(OperationRequest('q4', 'agent-1', 'build', 'test', frozenset({'build'})), 'a1', 'l3', verifier='agent-1')
    assert d.decision == Decision.DENY


def test_audit_chain_integrity():
    r = ManifexRuntime(); r.decide(OperationRequest('q5', 'agent-1', 'build', 'test', frozenset({'build'}))); assert r.audit.verify_chain()


def test_human_emergency_stop():
    r = ManifexRuntime(); r.emergency_stop(); assert r.state.value == 'TERMINATED' and not r.leases


if __name__ == '__main__':
    tests = [v for k, v in globals().items() if k.startswith('test_')]
    for test in tests:
        test()
    print(f'PASS {len(tests)} tests')
