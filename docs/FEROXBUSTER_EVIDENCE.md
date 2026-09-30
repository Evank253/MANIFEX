# MANIFEX Feroxbuster Evidence Collector

This adapter adds Feroxbuster as a **discovery-only** evidence-acquisition tool.

## Purpose

Find web resources that a normal crawl may miss, then preserve the discovery
output as an evidence candidate for MANIFEX qualification.

Pipeline:

`authorized target -> discovery -> raw artifact -> SHA-256 -> provenance manifest -> qualification`

Discovery is **not** verification. A discovered path must still be acquired,
examined, independently corroborated, and assigned an evidence level.

## Guardrails

- The operator must explicitly pass `--authorized`.
- Only HTTP(S) targets are accepted.
- Feroxbuster must be installed separately.
- No exploitation or credential bypass is performed by this adapter.
- TLS verification is retained by default.
- Raw JSON and stderr are preserved and hashed.
- The manifest records tool version, command, target, timing, exit code, and
  artifact hashes.
- Initial qualification is `UNVERIFIED_DISCOVERY` / `NOT_MEASURED`.

## Example

`python -m manifex.tools.feroxbuster_evidence --target https://example.org --authorized`

Use only against systems you own or have explicit permission to test.
