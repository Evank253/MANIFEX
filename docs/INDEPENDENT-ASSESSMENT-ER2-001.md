# Independent Adversarial Assessment — ER-v2

**Assessment ID:** `IA-ER2-001`  
**Target:** `er-v2` at `b36d3bc87f36fb308e179bb83824bf2da9707bdd`  
**Classification:** INDEPENDENT ADVERSARIAL ASSESSMENT  
**Qualification:** NOT_QUALIFIED  
**Authorization:** NOT_REQUESTED

## Independence and execution boundary

The assessment was performed as a separate adversarial procedure against the recorded v2 receiver logic retrieved from GitHub. The evaluator did not use the v2 acceptance suite as the decision mechanism.

The execution used a source-derived independent harness rather than an exact repository checkout. Therefore this is **not exact commit-bound runtime evidence**. It is an independent adversarial assessment of the recorded implementation logic.

The target implementation was not modified by the assessment.

## Results

| ID | Attack | Result |
|---|---|---|
| IA-01 | Remove request payload and forge request hash | PASS — rejected |
| IA-02 | Remove result payload and forge result hash | PASS — rejected |
| IA-03 | Remove both payloads and recompute evidence hash | PASS — rejected |
| IA-04 | Mutate request payload while retaining hash | PASS — rejected |
| IA-05 | Mutate result payload while retaining hash | PASS — rejected |
| IA-06 | Recompute persisted evidence from persisted object alone | PASS — exact self-rehash |
| IA-07 | Drop hash-covered field | PASS — detected |
| IA-08 | Attempt qualification escalation | PASS — rejected |
| IA-09 | Attempt authority escalation | PASS — rejected |
| IA-10 | Re-register duplicate execution identity | PASS — rejected |
| IA-11 | Surface-valid semantic identity deception | **FAIL — accepted** |

## IA-11 finding

The receiver correctly verifies:

- request payload → request hash
- result payload → result hash
- complete evidence object → evidence hash

However, it does not verify semantic identity relationships between the payloads and the surrounding evidence fields.

The adversarial case changed:

`request_payload.request_id = "attacker-request"`

while retaining:

`evidence.request_id = "req-1"`

The attacker then recomputed both the request hash and enclosing evidence hash.

All cryptographic checks therefore remained valid, and the receiver accepted the packet.

This demonstrates:

> **Cryptographic integrity of fields is not the same thing as semantic integrity between fields.**

The same class should be tested for at least:

- request_id
- mission_id
- execution_id
- evidence_id
- target commit
- command/phase relationships
- result identity relationships

## Assessment conclusion

The Experiment 001 defect class is fixed in the v2 implementation logic:

- omitted payloads no longer provide binding-free hashes;
- request/result mutations are detected;
- the persisted object is the hashed evidence object;
- field dropping is detectable;
- qualification and authority escalation remain blocked.

But ER-v2 is **not yet fully adversarially sound** because IA-11 found a new semantic-binding defect.

This is therefore **not a qualification pass**.

## Required next state

Do not patch the implementation inside this assessment.

Record this failure first.

Then define the next requirement revision specifically for semantic binding, followed by a new implementation and a new independent assessment.

The architecture has therefore produced exactly the kind of result the evidence doctrine requires: the evaluator was able to prove that the current implementation is still wrong in a previously untested dimension.

Raw result: `experiments/ia-er2-001-result.json`.
