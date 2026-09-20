# Capability Qualification Substrate (CQS) v0.1

CQS is a domain-neutral qualification protocol for converting proposed capabilities into versioned, evidence-backed capability states without granting authority.

## Architectural invariants

- Qualification is derived from immutable evidence; it is never self-declared.
- NOT_MEASURED is distinct from FAILED.
- Historical evidence is immutable; availability is derived.
- Qualified capability does not imply authorization.
- CQS does not own intelligence routing, authority, credentials, or execution.
- Domain profiles own qualification instruments; CQS owns the substrate contract.
- Every identity-bearing artifact is content-addressed.

## Status

DESIGNED / IMPLEMENTED (reference substrate) / NOT YET QUALIFIED AS A MANIFEX PRODUCTION COMPONENT.

The implementation is intentionally conservative: qualification requires an applicable profile, valid specification, required evidence, and successful profile evaluation.

## Layout

- `cqs/models.py` — immutable domain records and capability state.
- `cqs/evidence.py` — append-only evidence store.
- `cqs/profiles.py` — domain-neutral profile contract and example profiles.
- `cqs/evaluator.py` — qualification evaluation.
- `cqs/ledger.py` — hash-chained qualification ledger.
- `cqs/service.py` — orchestration facade.
- `cqs/api.py` — optional FastAPI adapter.
- `tests/` — deterministic unit tests.
