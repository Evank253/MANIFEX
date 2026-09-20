# CQS v0.1 Architecture

## Boundary

CQS qualifies capabilities. It does not grant authority, issue credentials, select models, route agents, or execute workloads.

## Evidence graph

Capability
-> Specification
-> Mechanism
-> Implementation
-> Qualification Profile
-> Benchmarks / Security / Reproduction
-> Runtime Evidence
-> Independent Replication
-> Independent Verification
-> Qualification Decision
-> Capability Availability

## State semantics

The human-readable lifecycle is:

PROPOSED -> SPECIFIED -> IMPLEMENTED -> TESTED -> BENCHMARKED -> SECURITY_REVIEWED -> REPRODUCED -> INDEPENDENTLY_VERIFIED -> QUALIFIED -> AVAILABLE

Internally, evidence dimensions remain independently addressable. A capability may have runtime evidence while security is NOT_MEASURED and independence is BLOCKED.

## Authority separation

QUALIFIED -> AVAILABLE

does not imply:

AVAILABLE -> AUTHORIZED

Authorization remains:

AVAILABLE -> INTELLIGENCE ROUTER -> PROPOSED EXECUTION -> AUTHORITY PLAN -> AUTHORIZATION -> LEASE -> EXECUTION

## Historical vs derived

Historical: specifications, benchmarks, results, runtime evidence, security evidence, replication, verification, qualification decisions.

Derived: availability, routing eligibility, specialist eligibility, model-selection eligibility, execution eligibility.

Derived state never rewrites historical state.
