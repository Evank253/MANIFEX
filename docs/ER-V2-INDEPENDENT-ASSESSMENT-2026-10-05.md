# Independent assessment — ER-v2 recorded implementation

**Assessment ID:** `ER-V2-ASSESS-001`  
**Status:** ADVERSARIAL RE-TEST / NOT QUALIFICATION  
**Date:** 2026-10-05  
**Subject:** `er-v2` at `b36d3bc87f36fb308e179bb83824bf2da9707bdd`  
**Frozen checkpoint:** `e110bcc5ac51068851fcf6d2179928b9aefa0ffd` (unchanged)  
**Requirements attacked:** ER2-R1, ER2-R2, ER2-R3, ER2-R4, ER2-R5  
**Out of scope:** P1, P2, P3, P4, P5

## Independence limit

This assessment attacked the recorded tree. It did not re-run the project's test file as the verdict. The assessor is the same assistant that wrote the v2 receiver, so this is an adversarial re-test, not a separate reviewer. That limit is part of the evidence. It does not by itself qualify or disqualify the fixes.

## Method

Packets were built in a fresh clone of `er-v2`. The ten required attacks were issued against `validate_packet`, `register_execution_evidence`, and `verify_persisted_evidence`. Additional probes were not in the acceptance list.

## Required attacks

| # | Attack | Result | Verdict |
|---|---|---|---|
| 1 | Missing `request_payload`, arbitrary 64-hex `request_hash` | REJECTED | FIXED |
| 2 | Missing `result_payload`, arbitrary 64-hex `result_hash` | REJECTED | FIXED |
| 3 | Both payloads missing, enclosing `evidence_hash` recomputed | REJECTED | FIXED |
| 4 | Request payload mutated, hash unchanged | REJECTED | FIXED |
| 5 | Result payload mutated, hash unchanged | REJECTED | FIXED |
| 6 | Persisted object alone recomputes `evidence_hash` | MATCH `904226c4c3e19ce4092047fcba15e1507fd514f5c51acb9d39971bd704db7329`; extra field survived | FIXED |
| 7 | Hash-covered field removed before verification | REJECTED | FIXED |
| 8 | `qualification_status=QUALIFIED`, and an integrity-passing registration | REJECTED; registered record stayed `NOT_QUALIFIED` / `NOT_MEASURED` / `DISCOVERED` | FIXED |
| 9 | `authority_decision_requested=true` | REJECTED | FIXED |
| 10 | Same `execution_id` registered twice | REJECTED | FIXED |

Hash `904226c4…` is from this assessment's packet. It is not the Experiment 001 hash and not the Experiment 002 hash `98234258…`.

## Additional probes

| Probe | Result | Reading |
|---|---|---|
| v1 schema packet | REJECTED | Schema boundary holds. v2 does not rewrite v1. |
| `request_payload` null | REJECTED | Fail closed. |
| Uppercase request hash | REJECTED | Not treated as binding. |
| Field added after evidence hash | REJECTED | Stale enclosing hash detected. |
| Nested payload edited on the persisted file | REJECTED | Binding checked on the persisted object. |
| `qualification_requested` set to the string `"false"` | REJECTED | Only boolean false is accepted. |
| Empty request payload with a matching hash | ACCEPTED | Binding holds. Not a defect. |
| Tuple inside a payload | Registered; persisted JSON recomputed to the same hash | JSON has no tuples; `canonical_hash` already serializes them as lists. No mismatch observed. |
| `authority_granted: true` stored as an evidence field, packet flag still false | ACCEPTED | Not an authority grant. No authority artifact was created. The field is hashed evidence, not a decision. Not scored as an ER2 failure. |

No new integrity defect was demonstrated in this pass.

## Verdict

Under the tested conditions, the Experiment 001 failure classes and the ten required attacks are FIXED on the recorded v2 receiver.

This verdict is not qualification. A same-author adversarial re-test cannot close the independence gap. Authorization was not requested. P1–P5 were not assessed.

## Boundaries

- Qualification: NOT_QUALIFIED
- Authorization: NOT_REQUESTED
- Next gate: a separate reviewer, or an explicit qualification experiment, still required before any qualification claim
