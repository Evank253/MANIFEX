# MANIFEX Engineering Gate v1

Status: CONSTITUTIONAL ENGINEERING INVARIANT

Every MANIFEX code change, integration, repair, benchmark, and deployment candidate must pass through the designated development and verification toolchain.

## Required lifecycle

MANIFEX CHANGE -> DEVELOPMENT TOOL -> UNDERSTAND -> IMPLEMENT/MODIFY -> TYPE CHECK -> LINT -> UNIT TESTS -> INTEGRATION TESTS -> E2E TESTS -> SECURITY TESTS -> CONSTITUTIONAL TESTS -> BUILD -> DEPLOYMENT REHEARSAL -> FAILURE INJECTION -> FIX -> RE-RUN EVERYTHING -> VERIFIED -> DEPLOY

## Required checks

- Code correctness
- Language/type errors
- Lint/static analysis
- Dependency resolution and compatibility
- API/interface compatibility
- Unit, integration, and end-to-end behavior
- Security vulnerabilities and adversarial cases
- Authorization and capability boundaries
- Sandbox and resource boundaries
- Runtime and deployment behavior
- Regression detection
- Provenance and reproducibility
- Audit completeness and integrity
- Constitutional invariant enforcement
- Performance and resource limits
- Failure recovery and termination behavior

## Verification rule

An agent, model, developer tool, or human may propose that code works. That proposal is not evidence of correctness. `VERIFIED` requires executable evidence from the required gate stages.

If a required gate cannot run, the result is `NOT MEASURED` or `BLOCKED`; it is never silently promoted to `VERIFIED`.

## Integration rule

MANIFEX capabilities integrate through explicit interfaces and adapters. Imported systems do not inherit MANIFEX authority merely because they are integrated. No adapter means no integration.

## Governance boundary

The development tool is an engineering instrument under MANIFEX constitutional control. It cannot modify the constitutional root, grant authority, bypass authorization, disable safety, disable audit, suppress evidence, or prevent authorized human termination.

## Evidence requirements

Each release candidate should retain, at minimum:

- source revision and provenance
- dependency lock information
- build identity
- test results
- security results
- constitutional results
- deployment rehearsal result
- failure-injection result
- environment identity
- artifact hashes
- verification identity
- final gate decision

## Release states

`DRAFT -> TESTING -> BLOCKED/FAILED -> FIXING -> RETESTING -> VERIFIED -> RELEASED`

A failed or incomplete gate cannot transition directly to `VERIFIED`.
