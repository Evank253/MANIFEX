# Experiment 002 — ER-v2 attack-class replay

**Experiment ID:** `EXP-002-ER-V2-ATTACK-REPLAY`  
**Status:** LOCAL EXECUTION / NOT QUALIFICATION  
**Requirements:** ER2-R1, ER2-R2, ER2-R3, ER2-R4, ER2-R5  
**Frozen v1 checkpoint:** `e110bcc5ac51068851fcf6d2179928b9aefa0ffd` (unchanged)

This record is the durable copy of a local replay. GitHub was not the execution environment.

The replay is source-equivalent to the Experiment 001 attack class. It is not a byte-identical rerun, and it does not replace Experiment 001 hashes.

## Cases

1. Legitimate v2 packet: ACCEPTED.
2. Request payload mutated, hash unchanged: REJECTED.
3. Payloads omitted, request hash 64 zeros, result hash 64 `f`, evidence hash recomputed: REJECTED.
4. Registration of that attack packet: REJECTED.
5. Legitimate packet persisted; recomputed hash matched stored hash `98234258558614c8c39167de155a743d77f2733439035e19f4351316c80c2dc5`. Extra field survived.

## Experiment 001 failure modes under this replay

| Mode | Result |
|---|---|
| Omitted payload + arbitrary hash accepted | FIXED |
| Attack packet registered | FIXED |
| Persisted projection cannot reproduce evidence hash | FIXED |

Qualification: NOT_QUALIFIED. Authorization: NOT_REQUESTED.

Raw result: `experiments/exp002-local-result.json`.
