# Human AI Companion

**Human AI Companion is its own product and system.** It is currently housed in the MANIFEX repository only as a controlled development location; it is not part of MANIFEX's pre-existing runtime, governance state, agent fabric, or application logic.

## Standalone boundary

The Companion owns its own:

- identity of the companion subject
- Personal / Development / Professional worlds
- privacy and consent rules
- memories and Life Log
- learning and tutoring state
- capability discovery
- evidence and provenance contracts
- capability passport
- credentials
- professional profile and opportunity matching
- companion provider interface
- companion runtime contracts

The package uses only its own modules and Python standard-library primitives. It must not import or mutate pre-existing MANIFEX systems.

## Relationship to MANIFEX

There is **no automatic integration** with the previously built MANIFEX systems.

If integration is ever desired, it will be a separate, explicit adapter boundary after the Companion is independently implemented, tested, secured, and verified. The Companion remains the owner of its product behavior and constitutional rules.

This prevents the previous MANIFEX architecture from silently becoming part of the Companion and prevents Companion state from silently becoming MANIFEX state.

## Worlds

- **Personal:** private Life Log, memory, reflection, emotional support.
- **Development:** learning, tutoring, assessment, practice, projects, discovery, verification.
- **Professional:** explicitly consented capability evidence, credentials, portfolio, profile, and opportunity matching.

Cross-world movement is denied by default and requires explicit, purpose-bound consent.

## Authority

Human authority is sovereign. The Companion cannot diagnose, manipulate, control life decisions, replace human relationships, determine human worth, or make consequential decisions on a person's behalf.

## Evidence

Capability claims require an evidence trail and provenance. A credential is a conclusion backed by evidence; it is not itself the underlying evidence.

## Current status

This is an **independent Companion build in progress**. The current branch contains its own foundation and runtime contracts. It is not yet represented as production-complete, externally verified, or fully deployed.
