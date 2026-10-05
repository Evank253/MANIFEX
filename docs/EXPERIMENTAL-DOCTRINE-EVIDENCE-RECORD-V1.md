# Evidence Record v1 — Experimental Doctrine

Status: FROZEN IMPLEMENTATION BASELINE
Milestone: Evidence Record v1 -> End-to-End Experimental Validation
Date: 2026-10-04

## Purpose

Evidence is a record of reality, not a mechanism for manufacturing success.

Evidence Record v1 is therefore frozen as an implementation baseline. No architectural expansion or feature additions should be made to this layer unless the end-to-end experiment exposes an actual defect or an unmet requirement.

## Frozen state

- Kronos execution contract: IMPLEMENTED
- Kronos evidence generation: IMPLEMENTED
- MANIFEX evidence receiver: IMPLEMENTED
- First-class evidence storage: IMPLEMENTED
- Hash recomputation: IMPLEMENTED
- Duplicate protection: IMPLEMENTED
- Append-only evidence ledger: IMPLEMENTED
- BuildIndex integration: IMPLEMENTED
- Qualification separation: PRESERVED
- Exact source checkout: BLOCKED
- Commit-bound execution: NOT ESTABLISHED
- End-to-end execution: PENDING
- Independent verification: NOT STARTED
- Qualification: NOT QUALIFIED

## Experimental chain

EXACT CHECKOUT
-> CONTROLLED EXECUTION
-> ExecutionResult
-> KRONOS EVIDENCE v1
-> MANIFEX INTEGRITY VERIFICATION
-> FIRST-CLASS EVIDENCE RECORD
-> EVIDENCE LEDGER
-> BuildIndex
-> QUALIFICATION GATE

The eventual experiment must bind the source revision, environment, request, execution, result, evidence, hashes, registration, ledger event, BuildIndex asset, and qualification decision.

## Acceptance dimensions

### 1. Integrity

MANIFEX must reject mutation of:

- request payload
- result payload
- evidence record

### 2. Provenance

The experiment must establish:

- exact source revision
- recorded environment
- exact execution request
- exact command and phase
- execution identity
- result identity
- evidence identity

### 3. Non-escalation

Registration must preserve:

- qualification_status = NOT_QUALIFIED or NOT_MEASURED

Registration must reject attempts to inject:

- qualification_status = QUALIFIED
- authority_decision_requested = true

### 4. Authority separation

Execution evidence is not authorization.

Kronos executes.
Evidence Record records.
MANIFEX verifies integrity and preserves provenance.
Qualification determines whether evidence is sufficient.
Human authority authorizes consequential action.

## Symmetric result doctrine

- PASS -> recorded as PASS
- FAIL -> recorded as FAIL
- BLOCKED -> recorded as BLOCKED
- TAMPERED -> rejected and recorded as an integrity failure
- ESCALATED -> rejected
- UNKNOWN -> remains UNKNOWN / NOT_MEASURED

A failure is not erased because it is inconvenient. A blocked provider is not converted into a test failure or a success claim. Missing evidence is not inferred.

## Required experiment package

At minimum:

- experiment_id
- Kronos repository
- Kronos commit SHA
- MANIFEX repository
- MANIFEX commit SHA
- execution_id
- request_id
- mission_id
- provider
- command
- phase
- environment
- start time
- finish time
- exit code
- stdout
- stderr
- stdout hash
- stderr hash
- request hash
- result hash
- evidence hash
- MANIFEX registration result
- BuildIndex asset ID
- ledger event
- qualification decision

A top-level experiment manifest hash should bind the complete package.

## Falsification rule

The evidence system must be capable of proving the architecture wrong.

If the experiment finds a hash mismatch, broken commit binding, mutable evidence, qualification bypass, authority escalation, or incorrect provider reporting, the failure is preserved as evidence and investigated. The implementation is not modified merely to make the experiment appear successful.

## Current execution blocker

Exact checkout/execution is currently blocked by the execution environment's inability to resolve GitHub. This is an environmental blocker, not a test result and not evidence that the implementation passes or fails.

## Next legitimate state transition

FROZEN IMPLEMENTATION
-> EXACT CHECKOUT AVAILABLE
-> CONTROLLED EXECUTION
-> EVIDENCE GENERATION
-> INTEGRITY VERIFICATION
-> MANIFEX REGISTRATION
-> IMMUTABLE EVIDENCE RECORD
-> QUALIFICATION DECISION

Do not redesign Evidence Record v1 before this experiment produces an actual defect or unmet requirement.
