"""
ManifexBridge – thin adapter that gives MANIFEX (Engineering Intelligence &
Execution OS) the same Integration Layer capabilities used by the Super
Cognitive Ecosystem: identity, provenance, events, agents, and health.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "integration_layer") not in sys.path:
    sys.path.insert(0, str(_ROOT / "integration_layer"))

from data_fabric import ProvenanceSync, ProvenanceRecord
from service_mesh import SubsystemRegistry, SubsystemInfo, SubsystemStatus, HealthMonitor
from identity_federation import UnifiedIdentity, IdentityRecord, IdentityType, PermissionBridge, AccessDecision
from event_orchestration import GlobalEventBus, Event  # type: ignore


class ManifexBridge:
    """Single entry point for MANIFEX to use the Integration Layer."""

    def __init__(self) -> None:
        self.registry = SubsystemRegistry()
        self.health = HealthMonitor(self.registry)
        self.identity = UnifiedIdentity()
        self.permissions = PermissionBridge()
        self.provenance = ProvenanceSync()
        self.events = GlobalEventBus()
        self._bootstrapped = False

    def bootstrap(self) -> None:
        if self._bootstrapped:
            return
        # Register MANIFEX core capabilities
        cores = [
            ("manifex-build", "Build Engine", ["build", "compile"]),
            ("manifex-secure", "Security & Verification", ["secure", "verify"]),
            ("manifex-govern", "Governance", ["policy", "approval"]),
            ("manifex-deploy", "Deployment", ["deploy", "operate"]),
            ("manifex-execute", "Execution Runtime", ["runtime", "agent"]),
        ]
        for sid, name, caps in cores:
            self.registry.register(SubsystemInfo(
                subsystem_id=sid,
                name=name,
                phase="MANIFEX",
                version="0.1.0",
                endpoints={"default": f"internal://{sid}"},
                capabilities=caps,
                status=SubsystemStatus.HEALTHY,
            ))
        self.permissions.mark_human_gated("deploy", "release")
        self.permissions.mark_human_gated("agent", "promote")
        self._bootstrapped = True
        self.events.publish(Event(
            event_type="manifex.bridge.bootstrapped",
            source="manifex_bridge",
            payload={"cores": len(cores)},
        ))

    def record_action(
        self,
        *,
        subject_id: str,
        subject_type: str,
        action: str,
        actor_id: str,
        content: Any,
        parent_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProvenanceRecord:
        rec = ProvenanceRecord.create(
            subject_id=subject_id,
            subject_type=subject_type,
            action=action,
            actor_id=actor_id,
            content=content,
            parent_ids=parent_ids,
            metadata=metadata or {},
        )
        self.provenance.record(rec)
        self.events.publish(Event(
            event_type=f"provenance.{action}",
            source="manifex_bridge",
            payload={"record_id": rec.record_id, "subject_id": subject_id},
        ))
        return rec

    def export_evidence(self, subject_id: str) -> Dict[str, Any]:
        return self.provenance.export_evidence_package(subject_id)

    def status(self) -> Dict[str, Any]:
        return {
            "bootstrapped": self._bootstrapped,
            "subsystems": len(self.registry.list_all()),
            "provenance_records": len(self.provenance._records),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
