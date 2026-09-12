# Human AI Companion — Standalone Architecture Boundary

## Decision

The Human AI Companion is a standalone product/system. Its presence inside the MANIFEX repository is a source-control location, not proof that it is part of the pre-existing MANIFEX runtime.

## Isolation rule

The Companion must not:

- import pre-existing MANIFEX application modules;
- mutate pre-existing MANIFEX state;
- inherit MANIFEX credentials, identity, memory, evidence, governance, agents, tools, or runtime permissions implicitly;
- treat MANIFEX outputs as Companion evidence without an explicit adapter and provenance record;
- expose Companion personal data to MANIFEX or third parties without the Companion's explicit consent policy.

## Companion-owned subsystems

Identity boundary, Personal/Development/Professional worlds, privacy, consent, memory, Life Log, learning, tutoring, assessment, discovery, capability evidence, provenance, passport, credentials, professional profile, opportunity matching, companion provider contract, and Companion runtime belong to this product.

## Future integration

Integration with MANIFEX is optional and must occur through explicit adapters. Each adapter must declare source, target, permissions, data classes, purpose, provenance, evidence requirements, failure behavior, and human-approval requirements.

**No adapter means no integration.**

## Product boundary

MANIFEX can later provide infrastructure services to the Companion, but infrastructure provision is not ownership of Companion product state or authority. The Companion remains sovereign over its own product contract.
