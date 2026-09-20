"""Canonical content hashing utilities."""

from __future__ import annotations
import hashlib
import json
from dataclasses import asdict, is_dataclass
from typing import Any


def canonicalize(value: Any) -> Any:
    if is_dataclass(value):
        return canonicalize(asdict(value))
    if isinstance(value, dict):
        return {str(k): canonicalize(value[k]) for k in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [canonicalize(v) for v in value]
    if hasattr(value, "value") and not isinstance(value, (str, bytes)):
        return value.value
    return value


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def content_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()
