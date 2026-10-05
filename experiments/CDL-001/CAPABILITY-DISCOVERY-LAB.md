# Capability Discovery / Composition Lab 001

Status: EXPERIMENTAL
Source repository: Evank253/MANIFEX
Source commit: b231f11b85651a230e2c9744f79501b85b54b77a
Source tree: 659021a7645e738a5092384e714c3e8e91d691b4
Experimental branch: experiment/capability-discovery-lab-001

## Preservation boundary

The source commit above is immutable for this experiment. No source-history rewrite is permitted. All discovery work occurs on the experimental branch.

## Objective

Determine what system-level capabilities can be produced by composing capabilities already present in MANIFEX, and determine which observations are merely hypotheses versus executable evidence.

## Questions

1. What capabilities are explicitly implemented?
2. What capabilities are latent in combinations of existing components?
3. Can a composite capability become a reusable primitive?
4. How does composition depth affect reliability, performance, and security?
5. Can useful compositions be discovered systematically?
6. Can compositions be automatically tested and adversarially challenged?
7. Does the containment architecture prevent authority escalation through composition or delegation?
8. What are the actual architectural limits?

## Initial evidence discovered during source audit

- The README defines a constitutional control plane: Human authority -> Constitution -> Safety -> Authorization -> Capability lease -> Sandbox -> Execution -> Audit -> Verification -> Evidence.
- MANIFEX-CONTAINMENT-INVARIANT.md explicitly prohibits authority/capability escalation through composition or delegation and requires reproducible adversarial evidence.
- MANIFEX-ENGINEERING-GATE.md defines a development-to-verification lifecycle including unit, integration, E2E, security, constitutional, failure-injection, and evidence stages.
- manifex_core/engine.py contains explicit constitutional invariants including non-transitive authority, no self-granted authority, no authority increase through AI action, and no self-verification of consequential actions.
- manifex_core/runtime.py implements human-issued authorizations, bounded capability leases, revocation, and emergency stop.
- tests/test_composition_security.py contains explicit tests for proxy capability non-transitivity, unauthorized network/filesystem access, isolation, constitutional modification denial, expired leases, and audit of denial.
- tests/test_e2e.py contains positive authorization and negative constitutional/authorization/self-verification/emergency-stop tests.

These observations establish implemented mechanisms in the source tree. They do NOT by themselves establish production qualification or universal non-bypassability.

## Experiment lifecycle

Inventory -> Compose -> Execute -> Test -> Adversarial Test -> Measure -> Preserve Evidence -> Qualify/Reject -> Candidate Integration

## Evidence states

HYPOTHESIS
IMPLEMENTED
EXECUTED
MEASURED
VERIFIED
QUALIFIED
NOT_MEASURED
BLOCKED

No experiment may promote a capability to VERIFIED or QUALIFIED without the corresponding evidence.

## First discovery target

Use the existing authorization + lease + containment + sandbox + audit + verification mechanisms as composable primitives and determine whether they can produce a higher-level governed capability that can itself be registered as a reusable primitive without gaining authority transitively.
