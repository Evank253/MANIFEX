# Independent assessment of ER-v2

**Assessment ID:** `IA-ER-V2-001`  
**Status:** INDEPENDENT ASSESSMENT / NOT QUALIFICATION  
**Date:** 2026-10-05  
**Assessed ref:** `er-v2` @ `b36d3bc87f36fb308e179bb83824bf2da9707bdd`  
**Frozen checkpoint:** `e110bcc5ac51068851fcf6d2179928b9aefa0ffd` (untouched)  
**Requirements in scope:** ER2-R1, ER2-R2, ER2-R3, ER2-R4, ER2-R5  
**Out of scope:** P1, P2, P3, P4, P5

This assessment attacked the recorded receiver. It did not treat the project's own tests as the result. GitHub was not the execution environment.

## Verdict on the ten claimed fixes

| Attack | Result |
|---|---|
| Missing `request_payload` + arbitrary 64-hex `request_hash` | FIXED — rejected |
| Missing `result_payload` + arbitrary 64-hex `result_hash` | FIXED — rejected |
| Both payloads missing + recomputed `evidence_hash` | FIXED — rejected |
| Request payload mutated, hash unchanged | FIXED — rejected |
| Result payload mutated, hash unchanged | FIXED — rejected |
| Persisted object alone recomputes `evidence_hash` | FIXED — match `904226c4c3e19ce4092047fcba15e1507fd514f5c51acb9d39971bd704db7329`; extra field survived |
| Drop a hash-covered field, then verify | FIXED — mismatch detected; registration did not drop the field |
| Integrity-passing packet promoted to QUALIFIED | FIXED — rejected; registered status stayed `NOT_QUALIFIED` / `NOT_MEASURED` / `DISCOVERED` |
| `authority_decision_requested=true` | FIXED — rejected |
| Duplicate execution identity | FIXED — rejected |

These are results for the tested attacks only. They are not qualification.

The persisted hash above is from this assessment's packet. It is not the Experiment 001 hash and not the Experiment 002 hash `98234258…`.

## Schema boundary

A `manifex-execution-evidence/v1` packet was rejected before the v2 acceptance path. v2 rejects v1. It does not rewrite v1.

## New defect

**ND-1 — empty `command` crashes after the evidence file is written.**

A packet with `command: []`, matching payload hashes, and a recomputed evidence hash passed integrity checks. Registration then raised `IndexError: list index out of range` at `tests=[evidence_record.command[0]]`.

Observed residue:

- evidence file existed
- ledger was not written
- index record was not added

This is not a falsification of ER2-R1 through ER2-R5. It is a new defect on the registration path after validation. A later registration of the same `execution_id` is blocked by the leftover file.

## Observations that are not failures of the stated requirements

- A payload that is an empty object, or a string, is accepted when its hash matches. ER2-R1/R2 require presence and hash match, not object shape.
- The ledger event does not contain payloads. The persisted evidence file did recompute its hash. The ledger is not the self-verifying record.

## Boundaries

- Qualification: NOT_QUALIFIED
- Authorization: NOT_REQUESTED
- P1–P5: not assessed, not added
- Next state: not qualified. A qualification gate is not authorized by this assessment.
