# ER-v2 local implementation record

**Record ID:** `ER-V2-LOCAL-IMPL-001`  
**Status:** HISTORICAL EVIDENCE / NOT QUALIFICATION  
**Date:** 2026-10-05  
**Requirements:** ER2-R1, ER2-R2, ER2-R3, ER2-R4, ER2-R5  
**Out of scope:** P1, P2, P3, P4, P5

## Chain

`ER-v1 frozen` → `Experiment 001` → `ER-v2 specification` → `local ER-v2 implementation` → `30/30 tests` → `local replay` → `this record`

## Execution boundary

The implementation and tests were executed in a local working copy. That working tree had no upstream during execution. GitHub was the durable record after the run, not the execution environment. GitHub Actions was not used.

The session working copy was ephemeral. The recorded receiver is the file that passed the local suite. A later recording commit (`2d91c74`) briefly wrote the literal text `PLACEHOLDER` into `manifex/execution_evidence.py`. Commit `3857c0f` replaced that file with the tested receiver. The placeholder is historical noise, not the implementation.

## Frozen checkpoint

`e110bcc5ac51068851fcf6d2179928b9aefa0ffd` is unchanged. It remains the frozen ER-v1 checkpoint. This branch does not rewrite it.

## Schema boundary

ER-v2 schema is `manifex-execution-evidence/v2`. A packet with `manifex-execution-evidence/v1` is rejected and is not accepted as v2.

## Local test result

30/30 tests passed on the local suite, including the thirteen ER-v2 acceptance tests and the v1-schema rejection test.

This is a test result. It is not qualification.

## Local replay of the Experiment 001 failure class

Source-equivalent replay against the v2 receiver. Not a byte-identical rerun of Experiment 001. The hashes below are not the Experiment 001 hashes.

| Case | Outcome |
|---|---|
| Legitimate v2 packet | ACCEPTED |
| Request payload mutated, hash unchanged | REJECTED |
| Payloads omitted, request hash 64 zeros, result hash 64 `f`, evidence hash recomputed | REJECTED |
| Registration of that attack packet | REJECTED |
| Persisted legitimate packet recomputes `evidence_hash` | MATCH |

Legitimate v2 persisted hash: `98234258558614c8c39167de155a743d77f2733439035e19f4351316c80c2dc5`. The extra field `kronos_only_field` survived persistence.

Experiment 001 failure classes under this replay:

- omitted payload + arbitrary hash accepted: FIXED
- attack packet registered: FIXED
- persisted projection cannot reproduce `evidence_hash`: FIXED

## Frozen v1 still reproduces the defect class

A source-equivalent replay of the same attack class against the frozen checkpoint file still accepted the omitted-payload packet and still failed to reproduce the evidence hash from the persisted projection (`c2281d19…` stored vs `cb49c517…` recomputed; extra field dropped). Those hashes are not the Experiment 001 hashes (`cc4424e9…` vs `b9afb0fb…`). The checkpoint replay is source-equivalent, not byte-identical.

## Boundaries

- Qualification: NOT_QUALIFIED
- Authorization: NOT_REQUESTED
- P1–P5: not included
- Next state: not qualified until this evidence is independently assessed and the qualification experiment or gate is completed
