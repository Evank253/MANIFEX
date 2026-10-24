"""Conservative capability classification for discovered assets."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Classification:
    capabilities: tuple[str, ...]
    confidence: float
    heuristic: bool = True


class CapabilityClassifier:
    def classify(self, signals: Iterable[str]) -> Classification:
        values = {str(x).lower() for x in signals}
        capabilities = tuple(sorted(values))
        return Classification(capabilities, 0.5 if capabilities else 0.0, True)
