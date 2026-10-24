"""Standalone Human AI Companion package.

This package intentionally depends only on its own modules and the Python
standard library. MANIFEX integration, if ever added, must live behind an
explicit adapter boundary and cannot become an implicit dependency.
"""

from .companion import HumanAICompanion
from .models import EvidenceState, World
from .runtime import CompanionRuntime

__all__ = ["HumanAICompanion", "CompanionRuntime", "EvidenceState", "World"]
