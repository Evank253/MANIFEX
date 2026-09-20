# MANIFEX Genesis Runtime

This branch is the executable foundation for the MANIFEX constitutional runtime.

## Integration contract

MANIFEX capabilities plug into one control plane through explicit contracts:

Human authority -> Constitution -> Safety -> Authorization -> Capability lease -> Sandbox -> Execution -> Audit -> Verification -> Evidence.

Imported systems are treated as capabilities, not authorities. Existing projects can be connected through adapters without granting them MANIFEX governance authority.

## Current executable foundation

- `manifex_core.models`: typed authorization, capability lease, operation, audit, evidence and decision objects.
- `manifex_core.engine`: constitutional decision engine and fail-closed invariant checks.
- `manifex_core.audit`: append-only in-process hash-chain audit ledger.
- `manifex_core.runtime`: runtime boundary for authorization, leases, revocation and emergency stop.
- `tests/test_e2e.py`: initial negative and positive constitutional benchmark.

## Evidence rule

A capability registry entry is not an implementation claim. Runtime behavior is qualified only by executable tests and preserved evidence.
