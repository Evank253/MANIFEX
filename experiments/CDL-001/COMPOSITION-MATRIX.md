# CDL-001 Composition Matrix

Status: DISCOVERY DESIGN — no qualification implied.

Source:
- Repository: Evank253/MANIFEX
- Protected commit: b231f11b85651a230e2c9744f79501b85b54b77a
- Protected tree: 659021a7645e738a5092384e714c3e8e91d691b4
- Experimental branch: experiment/capability-discovery-lab-001

## Discovery rule

A composition is a candidate capability only if its constituent interfaces can be connected without granting authority that no constituent legitimately possesses. Every candidate must be tested at the execution boundary and its evidence state recorded.

## Candidate compositions

| ID | Composition | Candidate system-level capability | Status |
|---|---|---|---|
| C-001 | authorization + capability lease + manifest + containment + sandbox + audit | governed execution | HYPOTHESIS |
| C-002 | C-001 + test harness + evidence capture | governed test execution | HYPOTHESIS |
| C-003 | C-002 + adversarial security tests + verification gate | self-evaluating execution pipeline | HYPOTHESIS |
| C-004 | capability inventory + composition rules + C-003 | capability qualification pipeline | HYPOTHESIS |
| C-005 | C-004 + reusable qualified composite registry | compositional capability reuse | HYPOTHESIS |

## Required measurements

For each candidate:
1. Can the composition execute its intended operation?
2. Does every constituent retain its original authority boundary?
3. Does any component acquire authority transitively?
4. Can an expired/revoked capability be reused through the composite?
5. Can the composite reach an unauthorized network/filesystem/action?
6. Is the attempted operation completely represented in the audit trail?
7. Can the composite certify its own consequential result?
8. What is the composition depth?
9. What latency and failure rate are observed?
10. Does the candidate remain valid when nested inside another composition?

## Evidence states

NOT_MEASURED → EXECUTED → MEASURED → VERIFIED → QUALIFIED

A source declaration or passing-looking code path never substitutes for execution evidence.

## Promotion rule

A candidate remains HYPOTHESIS until reproducible execution evidence exists. A composite cannot become a reusable primitive merely because it is useful; it must pass the same authority, containment, audit, verification, and regression requirements applied to ordinary capabilities.

## Immediate first wave

Run C-001 and C-002 first. They establish whether ordinary MANIFEX execution primitives compose into a higher-level governed execution/test capability before attempting recursive discovery.
