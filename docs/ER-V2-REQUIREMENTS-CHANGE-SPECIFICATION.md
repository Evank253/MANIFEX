# Evidence Record v2 — Requirements & Change Specification

**Specification ID:** `ER-V2-REQ-001`  
**Status:** REQUIREMENTS-ONLY / NOT IMPLEMENTED  
**Date:** 2026-10-04  
**Causal source:** `EXP-001-ER-V1-INTEGRITY-FALSIFICATION`  
**Frozen source references:** MANIFEX `e110bcc5ac51068851fcf6d2179928b9aefa0ffd`; Kronos `6bd20041d4ac34e5254f405a0c7d5587ee676bda`

## 1. Purpose

Define the Evidence Record v2 engineering requirements directly from Experiment 001.

This document is a change specification, not an implementation and not qualification evidence. ER-v1 remains historically frozen and must not be retroactively modified to incorporate these requirements.

The governing evolution chain is:

`Observation → Experiment → Evidence → Requirement → Engineering Change → New Experiment`

No v2 implementation change should be presented as justified by an explanation written after the change. Each v2 change must trace to a requirement in this specification, and each requirement must trace either to the experimentally demonstrated findings of Experiment 001 or to a separately scoped proposed requirement.

## 2. Historical Boundary

ER-v1 state:

**FROZEN / EXPERIMENTALLY FALSIFIED ON TESTED INTEGRITY PROPERTY**

Experiment 001 established two experimentally demonstrated defects:

1. The v1 receiver accepts request/result hashes without corresponding payloads, provided the hashes have valid SHA-256 shape and the enclosing evidence hash is valid.
2. The MANIFEX first-class persistence path projects the evidence object and can discard fields needed to independently reconstruct the original evidence hash.

These findings are the causal basis for the mandatory v2 requirements below.

The exact-checkout limitation of Experiment 001 remains part of its evidence. The experiment used a controlled source-equivalent reconstruction and is not claimed as exact commit-bound execution.

## 3. ER-v2 Mandatory Requirements

### ER2-R1 — Unconditional Request Hash Binding

A request hash MUST NOT be accepted unless the corresponding canonical request payload is present and available to the verifier.

The verifier MUST recompute the canonical request hash from the supplied request payload and compare it with the supplied request hash.

A syntactically valid 64-hex request hash MUST NOT be treated as evidence of binding by itself.

**Causal basis:** Experiment 001 — omitted request payload + arbitrary request hash was accepted.

### ER2-R2 — Unconditional Result Hash Binding

A result hash MUST NOT be accepted unless the corresponding canonical result payload is present and available to the verifier.

The verifier MUST recompute the canonical result hash from the supplied result payload and compare it with the supplied result hash.

A syntactically valid 64-hex result hash MUST NOT be treated as evidence of binding by itself.

**Causal basis:** Experiment 001 — omitted result payload + arbitrary result hash was accepted.

### ER2-R3 — Self-Verifiable Persisted Evidence

The persisted MANIFEX evidence record MUST retain the complete evidence object used to calculate `evidence_hash`, or retain an explicitly specified cryptographically equivalent representation from which the exact hashed object can be reconstructed without relying on omitted upstream state.

A verifier reading only the persisted record MUST be able to recompute and independently verify the recorded `evidence_hash`.

The persisted record MUST NOT claim self-verifiable evidence integrity when fields material to the evidence hash have been discarded.

**Causal basis:** Experiment 001 — persisted projection could not reproduce the original evidence hash.

### ER2-R4 — Persisted/Hashed Object Identity

The v2 specification MUST define exactly which canonical object is hashed as `evidence_hash`.

The persisted representation MUST preserve that object's identity sufficiently to reproduce the exact hash.

Any transformation from incoming evidence to persisted evidence MUST be explicit and testable. Silent projection, field dropping, or schema reshaping MUST NOT invalidate independent verification.

**Causal basis:** Experiment 001 demonstrated divergence between the hashed upstream object and the persisted MANIFEX projection.

### ER2-R5 — Fail Closed on Missing Binding Material

If any material payload required to verify a request hash, result hash, or evidence hash is absent, malformed, or otherwise unavailable, verification MUST fail closed.

The system MUST NOT infer integrity from hash syntax, metadata completeness, source labels, or a caller assertion.

The resulting state MUST remain an explicit failure/unknown/not-measured state as appropriate and MUST NOT escalate to qualification or authorization.

**Causal basis:** Direct consequence of both experimentally demonstrated integrity failures.

## 4. Required v2 Acceptance Tests

Implementation is not complete until tests demonstrate all of the following:

1. Valid request payload + matching request hash is accepted.
2. Valid result payload + matching result hash is accepted.
3. Request payload mutation with unchanged hash is rejected.
4. Result payload mutation with unchanged hash is rejected.
5. Missing request payload + arbitrary request hash is rejected.
6. Missing result payload + arbitrary result hash is rejected.
7. Missing request/result payloads + recomputed enclosing evidence hash is rejected.
8. Persisted evidence can independently reproduce its recorded evidence hash using only persisted material.
9. Mutation of any field covered by the evidence hash is detected.
10. Dropping a hash-covered field before persistence is detected or prohibited.
11. Re-registration of the same execution identity remains governed by explicit duplicate/immutability rules.
12. v2 cannot promote a record to qualification merely because its integrity checks pass.
13. v2 cannot create or request consequential authority merely because evidence registration succeeds.

These are acceptance requirements, not yet executed test results.

## 5. Explicit Non-Goals for This Revision

The following are NOT to be silently folded into ER-v2 implementation solely because they appeared in the Grok assessment. They require formal scope and, where appropriate, separate experiments or acceptance criteria:

- actual checkout/commit verification;
- stronger evidence immutability beyond the integrity requirements above;
- tighter BuildIndex ↔ evidence qualification coupling;
- preservation of every field currently discarded by the projection, except where required to satisfy self-verification;
- a complete formal canonicalization standard beyond defining the exact hashed object and deterministic encoding required by ER2-R4.

These remain **proposed follow-on requirements** until separately scoped.

## 6. Proposed Follow-on Requirement Areas

### P1 — Actual Checkout/Commit Verification

Determine whether a claimed target commit is cryptographically tied to the source actually executed, rather than merely recorded as a string.

Status: **PROPOSED / NOT EXPERIMENTALLY RESOLVED**

### P2 — Evidence Immutability

Determine the required append-only, content-addressed, or otherwise tamper-evident persistence model for evidence records and ledgers.

Status: **PROPOSED / NOT EXPERIMENTALLY RESOLVED**

### P3 — BuildIndex Qualification Coupling

Determine whether BuildIndex transitions can currently bypass evidence requirements and define the correct enforcement boundary.

Status: **PROPOSED / NOT EXPERIMENTALLY RESOLVED**

### P4 — Projection Field Preservation

Audit the complete Kronos evidence schema against the MANIFEX projection and determine which fields must remain first-class for provenance, replay, integrity, and independent verification.

Status: **PROPOSED / NOT EXPERIMENTALLY RESOLVED**

### P5 — Canonicalization Specification

Define and test a stable canonicalization contract covering payload encoding, field ordering, types, null handling, Unicode, and serialization behavior.

Status: **PROPOSED / NOT EXPERIMENTALLY RESOLVED**

## 7. Traceability

| Requirement | Source | Status |
|---|---|---|
| ER2-R1 Request hash binding | Experiment 001 omitted-payload attack | REQUIRED |
| ER2-R2 Result hash binding | Experiment 001 omitted-payload attack | REQUIRED |
| ER2-R3 Self-verifiable persistence | Experiment 001 persistence mismatch | REQUIRED |
| ER2-R4 Persisted/hashed object identity | Experiment 001 projection mismatch | REQUIRED |
| ER2-R5 Fail-closed missing material | Experiment 001 integrity findings | REQUIRED |
| P1 Checkout/commit verification | Independent assessment | PROPOSED |
| P2 Evidence immutability | Independent assessment | PROPOSED |
| P3 BuildIndex coupling | Independent assessment | PROPOSED |
| P4 Projection field preservation | Independent assessment | PROPOSED |
| P5 Canonicalization | Independent assessment | PROPOSED |

## 8. Change-Control Rules

1. ER-v1 source and checkpoint documentation remain frozen.
2. No v2 change may alter the historical interpretation of Experiment 001.
3. Every implementation commit for ER-v2 MUST reference one or more ER2 requirement IDs.
4. Every new test MUST identify the requirement it is intended to verify.
5. A passing test demonstrates the tested property only; it does not by itself establish system-wide qualification.
6. A failed test MUST remain recorded as evidence and MUST NOT be rewritten into a success state.
7. Qualification remains separate from evidence registration.
8. Authority remains separate from execution and evidence registration.
9. No consequential authorization is implied by satisfying any ER2 requirement.

## 9. Required Experimental Closure

After implementation, ER-v2 MUST undergo a new experiment that includes at minimum:

- the original Experiment 001 attack cases;
- the new positive controls;
- persistence self-verification;
- mutation testing;
- missing-material testing;
- qualification non-escalation;
- authority non-escalation.

The new experiment must state whether each Experiment 001 failure mode is:

- FIXED;
- NOT FIXED;
- PARTIALLY FIXED;
- NOT REPRODUCIBLE under the tested conditions; or
- UNKNOWN.

No v2 requirement is considered experimentally closed merely because code exists.

## 10. Qualification Boundary

This specification establishes **requirements only**.

Current state remains:

- ER-v1: FROZEN / EXPERIMENTALLY FALSIFIED ON TESTED INTEGRITY PROPERTY
- Experiment 001: COMPLETED
- ER-v2 implementation: NOT STARTED
- ER-v2 qualification: NOT QUALIFIED
- Authorization: NOT REQUESTED

## 11. Governing Principle

**Evidence precedes engineering change. Engineering change precedes the next experiment.**

The purpose of ER-v2 is not to make the system appear correct. It is to make the previously demonstrated failure impossible under the defined acceptance conditions, and then to subject that claim to a new experiment capable of proving the revision wrong.
