# MANIFEX Architectural Containment Invariant v1

## Constitutional requirement

The MANIFEX LLM is architecturally bound to its authorized execution environment. It does not possess the authority, capability, credentials, interfaces, or enforcement privileges required to leave, expand, rewrite, circumvent, or recreate the boundaries of that environment.

The containment boundary is enforced outside the LLM reasoning process and is not dependent upon the LLM choosing to obey it.

## Prohibited boundary circumvention

No LLM-generated instruction, code, tool call, agent delegation, encoded message, prompt, indirect request, capability combination, or interaction with another system may:

- escape or bypass the authorized execution boundary;
- acquire unauthorized privileges, credentials, resources, or infrastructure;
- grant authority to itself or another agent;
- modify or disable the Safety Kernel, authorization system, audit system, emergency controls, or constitutional root;
- establish unauthorized persistence, replication, communication, or external control;
- create a system whose purpose is to circumvent the MANIFEX boundary;
- use another agent, model, tool, service, or system as an indirect path around a restriction;
- transform a denied capability into an equivalent capability through composition or delegation;
- conceal an attempted boundary violation.

## Non-transitive authority

**Authority is non-transitive. Capability is non-transitive. Delegation does not create authority. Intelligence does not create authority.**

A newly generated component inherits zero authority by default. It must independently receive an authorized capability lease.

## Independent enforcement

The LLM and MANIFEX Core are both subjects of the containment architecture. No component may establish, enlarge, modify, or remove the security boundary that constrains that component.

## Fail closed

If required containment, authorization, identity, audit, safety, monitoring, or verification becomes unavailable, uncertain, compromised, or unverifiable, consequential execution must be denied or terminated according to the applicable safety procedure.

## Human authority

Human authority remains external to and above the LLM and MANIFEX execution environment. Authorized humans retain the ability to revoke capabilities, isolate execution, terminate execution, inspect evidence, and change or terminate the system.

## Verification

Containment is a security property, not a behavioral promise. It must be supported by reproducible adversarial evidence covering direct escape, indirect escape, delegated escape, tool-mediated escape, generated-code escape, persistence, replication, covert communication, privilege escalation, credential acquisition, and cross-system capability escalation.

A containment claim is `VERIFIED` only to the extent supported by reproducible evidence. Otherwise it is `NOT MEASURED` or `BLOCKED`.
