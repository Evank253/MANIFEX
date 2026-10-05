# Experiment 001 — Evidence Record v1 Integrity Falsification

**Experiment ID:** `EXP-001-ER-V1-INTEGRITY-FALSIFICATION`

**Classification:** Experimental integrity result — NOT qualification evidence

**Date:** 2026-10-04

## Purpose

Test the strongest independent finding in the Grok historical assessment:

> Can the frozen MANIFEX Evidence Record v1 receiver accept an evidence packet with the request and result payloads omitted, arbitrary 64-hex request/result hashes supplied, and a correctly recomputed evidence hash?

A positive result would experimentally demonstrate the conditional request/result binding defect identified by independent inspection.

## Frozen Source References

- MANIFEX checkpoint: `e110bcc5ac51068851fcf6d2179928b9aefa0ffd`
- Kronos checkpoint: `6bd20041d4ac34e5254f405a0c7d5587ee676bda`

## Checkout Boundary

An exact Git checkout could not be established in the execution environment because DNS/network access to `github.com` was unavailable:

`fatal: unable to access 'https://github.com/Evank253/MANIFEX.git/': Could not resolve host: github.com`

Therefore this run is **not claimed as exact commit-bound execution**.

Instead, the experiment used a controlled source-equivalent reconstruction of the exact receiver logic inspected at the cited commits. This distinction is material and remains part of the evidence.

## Procedure

1. Construct a legitimate request/result/evidence packet matching the v1 schema.
2. Compute request hash and result hash using the implementation's `canonical_hash`.
3. Compute the evidence hash using the implementation's evidence-hash construction.
4. Submit the legitimate packet to the reconstructed receiver.
5. Confirm that ordinary request/result payload mutation is rejected.
6. Remove `request_payload` and `result_payload`.
7. Replace `request_hash` with 64 zeros.
8. Replace `result_hash` with 64 lowercase `f` characters.
9. Recompute `evidence_hash` over the modified evidence object.
10. Submit the modified packet.
11. Exercise the first-class persistence path.
12. Recompute an evidence hash using only the persisted MANIFEX projection.

## Results

### Control: legitimate packet

**Result: ACCEPTED**

The legitimate packet passed the receiver validation logic.

### Control: payload mutation

**Result: REJECTED**

When request or result payloads were present and modified without changing their hashes, the receiver rejected the packet because the recomputed payload hashes no longer matched.

This confirms that the receiver does enforce request/result binding **when the payload fields are present**.

### Falsification case: omitted payloads + arbitrary hashes

**Result: ACCEPTED**

The modified packet omitted both payloads and supplied:

- request hash: `0000000000000000000000000000000000000000000000000000000000000000`
- result hash: `ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff`

The receiver accepted the packet after the evidence hash was recomputed.

This is an **experimentally demonstrated integrity failure** in Evidence Record v1's request/result binding.

The receiver checks that the supplied hashes have the form of SHA-256 digests, but when the payloads are absent it does not require those hashes to be recomputed from payloads.

### Persistence experiment

The accepted attack packet was passed through the first-class MANIFEX registration path.

**Registration result: ACCEPTED**

The stored record was then rehashed using the same evidence-hash algorithm over the fields actually persisted.

For a packet containing the broader Kronos evidence fields, the result was:

- stored `evidence_hash`: `cc4424e9279dedd010a54eb578848d8d2e4d850ee2f141ff91712866f40aebe8`
- recomputed hash from persisted projection: `b9afb0fb2dca5c986a2c61e87aaa9853cc3ff2118f99252be44f75a59f36d7eb`
- match: **FALSE**

This experimentally confirms the second independent finding: the persisted MANIFEX record is a projection of the hashed evidence object and cannot independently reconstruct the original evidence hash when the upstream evidence contains fields that the projection drops.

## Evidence Summary

| Check | Result |
|---|---|
| Legitimate packet accepted | PASS |
| Request mutation rejected when payload present | PASS |
| Result mutation rejected when payload present | PASS |
| Omitted payloads + arbitrary request hash | **FAIL — accepted** |
| Omitted payloads + arbitrary result hash | **FAIL — accepted** |
| Evidence hash recomputed over attack packet | PASS |
| Attack packet registered by MANIFEX | **FAIL — accepted** |
| Persisted projection independently reproduces original evidence hash | **FAIL — mismatch** |
| Qualification granted | NO |
| Authority requested | NO |

## Raw Result Identity

Canonical result summary hash:

`039001822c7f004e7138fdb84c0d2d981704749c4e1e1e93f62f61239fc71850`

The summary included:

- experiment ID;
- source commit references;
- exact-checkout status;
- method;
- acceptance/rejection outcomes;
- arbitrary hashes used;
- attack evidence hash;
- persisted-record rehash;
- qualification and authority state.

## Environment

- OS: `Linux-6.18.44-x86_64-with-glibc2.41`
- Python: `3.13.5`
- Architecture: `x86_64`
- Git: `git version 2.47.3`

## Interpretation

Grok's strongest static finding is **confirmed by controlled execution of source-equivalent reconstruction**.

The frozen Evidence Record v1 implementation does not provide unconditional request/result hash binding.

The precise defect is:

`request_payload/result_payload absent` + `arbitrary 64-hex hashes` + `valid evidence_hash` → **receiver accepts**

The second finding is also confirmed for a full Kronos-shaped evidence object:

`hashed evidence object` → `MANIFEX first-class projection` → **stored projection cannot reproduce original evidence_hash**

## Historical Status

This experiment does **not** modify the frozen historical checkpoint.

It creates the first experimentally demonstrated defect record in the next evolutionary layer:

`Evidence Record v1 frozen`

→ `independent inspection`

→ `Experiment 001`

→ **integrity defect experimentally demonstrated**

→ `evidence-driven revision required`

No fix is included in this experiment.

## Qualification and Authority Boundary

This result is not qualification evidence establishing system success.

It establishes a failure of the frozen implementation under the tested condition.

Therefore:

- **Qualification:** `NOT_QUALIFIED`
- **Authorization:** `NOT_REQUESTED`
- **Evidence Record v1:** experimentally falsified on the tested integrity property
- **Next engineering action:** design and implement a revision only after this result is preserved as the causal basis

## Governing Principle

**The system recorded a result that makes the implementation look worse, rather than rewriting the result to make the implementation look successful.**

That is the intended behavior of the historical/evidence architecture.
