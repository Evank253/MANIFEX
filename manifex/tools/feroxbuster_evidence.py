#!/usr/bin/env python3
"""MANIFEX Feroxbuster Evidence Collector.

Runs the externally installed feroxbuster binary as a discovery-only acquisition
tool and preserves the raw JSON output plus a provenance manifest.

Safety model:
- Explicit --authorized acknowledgement is required.
- This module performs discovery only; it does not exploit discovered endpoints.
- TLS verification remains enabled unless the operator explicitly passes
  --insecure.
- Results are treated as evidence candidates, not verified facts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require_http_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise argparse.ArgumentTypeError("target must be an absolute http(s) URL")
    return value


def run(args: argparse.Namespace) -> int:
    if not args.authorized:
        raise SystemExit(
            "Refusing to scan: pass --authorized only when you are authorized "
            "to test the target."
        )

    binary = shutil.which(args.binary)
    if not binary:
        raise SystemExit(
            f"feroxbuster binary not found: {args.binary!r}. "
            "Install feroxbuster separately and ensure it is on PATH."
        )

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    safe_host = urlparse(args.target).netloc.replace(":", "_")
    raw_path = out_dir / f"feroxbuster-{safe_host}-{stamp}.json"
    manifest_path = out_dir / f"feroxbuster-{safe_host}-{stamp}.manifest.json"

    version_proc = subprocess.run(
        [binary, "--version"],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    version = (version_proc.stdout or version_proc.stderr).strip()

    cmd = [
        binary,
        "--url",
        args.target,
        "--json",
        "--output",
        str(raw_path),
        "--depth",
        str(args.depth),
        "--threads",
        str(args.threads),
        "--timeout",
        str(args.timeout),
    ]

    if args.rate_limit is not None:
        cmd += ["--rate-limit", str(args.rate_limit)]
    if args.wordlist:
        cmd += ["--wordlist", args.wordlist]
    for extension in args.extension:
        cmd += ["--extensions", extension]
    if args.no_recursion:
        cmd.append("--no-recursion")
    if args.extract_links:
        cmd.append("--extract-links")
    if args.insecure:
        cmd.append("--insecure")

    started = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    finished = time.time()

    # Feroxbuster writes JSON results to raw_path. Preserve stderr separately
    # because it can contain operational diagnostics useful during audit.
    stderr_path = raw_path.with_suffix(".stderr.txt")
    stderr_path.write_text(proc.stderr or "", encoding="utf-8")

    raw_sha = sha256_file(raw_path) if raw_path.exists() else None
    stderr_sha = sha256_file(stderr_path)

    manifest = {
        "schema": "MANIFEX-FEROXBUSTER-EVIDENCE-1",
        "tool": "feroxbuster",
        "tool_version": version,
        "target": args.target,
        "target_host": urlparse(args.target).netloc,
        "authorized_acknowledgement": True,
        "started_at_unix": started,
        "finished_at_unix": finished,
        "duration_seconds": round(finished - started, 3),
        "exit_code": proc.returncode,
        "command": cmd,
        "artifacts": {
            "raw_json": {
                "path": str(raw_path),
                "sha256": raw_sha,
            },
            "stderr": {
                "path": str(stderr_path),
                "sha256": stderr_sha,
            },
        },
        "qualification": {
            "status": "UNVERIFIED_DISCOVERY",
            "evidence_level": "NOT_MEASURED",
            "note": (
                "Discovery output identifies candidate resources. It does not "
                "establish ownership, content meaning, authenticity, or truth."
            ),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(manifest, indent=2, sort_keys=True))
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="MANIFEX Feroxbuster evidence collector")
    parser.add_argument("--target", required=True, type=require_http_url)
    parser.add_argument("--authorized", action="store_true")
    parser.add_argument("--binary", default="feroxbuster")
    parser.add_argument("--output-dir", default=".manifex/evidence/feroxbuster")
    parser.add_argument("--wordlist")
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--threads", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=7)
    parser.add_argument("--rate-limit", type=int)
    parser.add_argument("--extension", action="append", default=[])
    parser.add_argument("--no-recursion", action="store_true")
    parser.add_argument("--extract-links", action="store_true")
    parser.add_argument("--insecure", action="store_true")
    args = parser.parse_args()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
