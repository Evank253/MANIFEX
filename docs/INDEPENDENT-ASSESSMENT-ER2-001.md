# Independent Adversarial Assessment — ER-v2

**Assessment ID:** `IA-ER2-001`  
**Target:** `er-v2` at `b36d3bc87f36fb308e179bb83824bf2da9707bdd`  
**Classification:** INDEPENDENT ADVERSARIAL SOURCE ANALYSIS  
**Qualification:** NOT_QUALIFIED  
**Authorization:** NOT_REQUESTED

## Execution boundary

This record is an independent adversarial **source analysis**, not a runtime execution result. The evaluator retrieved the recorded v2 receiver and acceptance tests from GitHub and reasoned against the implementation logic. No claim is made that the attack harness was executed locally, and no exact-checkout runtime evidence is claimed.

The target implementation was not modified by the assessment.

## Findings

IA-01 through IA-10 are statically supported as rejected by the recorded receiver:

| ID | Attack | Static outcome |
|---|---|---|
| IA-01 | Remove request payload and forge request hash | REJECT — required field check |
| IA-02 | Remove result payload and forge result hash | REJECT — required field check |
| IA-03 | Remove both payloads and recompute evidence hash | REJECT — required payload checks |
| IA-04 | Mutate request payload while retaining hash | REJECT — request hash mismatch |
| IA-05 | Mutate result payload while retaining hash | REJECT — result hash mismatch |
| IA-06 | Recompute persisted evidence from persisted object alone | PASS — verifier hashes persisted object itself |
| IA-07 | Drop hash-covered field | DETECT — persisted evidence hash changes |
| IA-08 | Attempt qualification escalation | REJECT — only NOT_QUALIFIED/NOT_MEASURED accepted |
| IA-09 | Attempt authority escalation | REJECT — authority request must be false |
| IA-10 | Re-register duplicate execution identity | REJECT — existing evidence file blocks overwrite |

These are **source-level conclusions**, not executed test results.

## IA-11 — new defect

A surface-valid semantic identity deception is accepted by the receiver logic.

Construct an otherwise valid v2 packet and change:

`evidence.request_payload.request_id`

from `req-1` to another value, while leaving:

`evidence.request_id = "req-1"`

Then recompute:

- `request_hash` from the altered request payload;
- `evidence_hash` from the altered evidence object.

The receiver's checks all pass because it verifies the request payload against the request hash, but it does **not** verify that the payload's `request_id` agrees with the surrounding evidence's `request_id`.

Therefore the receiver accepts a cryptographically self-consistent packet whose semantic identities disagree.

This demonstrates:

> **Cryptographic integrity of fields is not the same thing as semantic integrity between fields.**

The same class should be examined for:

- request_id
- mission_id
- execution_id
- evidence_id
- target commit
- command/phase relationships
- result identity relationships

## Conclusion

The Experiment 001 defect class is addressed by the v2 implementation logic:

- omitted payloads no longer provide binding-free hashes;
- request/result mutations are detected;
- the persisted object is the hashed evidence object;
- field dropping is detectable;
- qualification and authority escalation remain blocked.

However, the independent source analysis identifies a new semantic-binding defect.

**ER-v2 therefore remains NOT_QUALIFIED.**

This assessment must not be represented as runtime execution evidence. A later exact/source-bound adversarial execution should attempt IA-11 and the other attacks before qualification.

## Required next state

Do not patch the implementation inside this assessment.

First preserve this finding. Then define the next requirement revision for semantic binding, implement it separately, and perform a new independent adversarial assessment.

Raw analysis result: `experiments/ia-er2-001-result.json`.
