from __future__ import annotations
import hashlib, json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from .models import AuditEvent

class AuditLedger:
    def __init__(self, path: str | Path | None = None, constitution_hash: str = "CONSTITUTION-v1"):
        self.path = Path(path) if path else None
        self.constitution_hash = constitution_hash
        self._events: list[AuditEvent] = []
        self._lock = RLock()

    @property
    def events(self):
        return tuple(self._events)

    @staticmethod
    def _canonical(d: dict) -> str:
        return json.dumps(d, sort_keys=True, separators=(",", ":"), default=str)

    def append(self, *, event_id: str, event_type: str, actor: str, request_id: str | None, authorization_id: str | None,
               capability_lease_id: str | None, action: str, state_before: str | None, state_after: str | None,
               decision: str | None, result: str | None, reason: str | None, input_hash: str | None = None,
               output_hash: str | None = None, evidence_refs: tuple[str, ...] = ()) -> AuditEvent:
        with self._lock:
            previous = self._events[-1].event_hash if self._events else "GENESIS"
            timestamp = datetime.now(timezone.utc)
            body = dict(event_id=event_id,event_type=event_type,timestamp=timestamp.isoformat(),actor=actor,
                        request_id=request_id,authorization_id=authorization_id,capability_lease_id=capability_lease_id,
                        action=action,state_before=state_before,state_after=state_after,decision=decision,result=result,
                        reason=reason,input_hash=input_hash,output_hash=output_hash,constitution_hash=self.constitution_hash,
                        previous_event_hash=previous,evidence_refs=evidence_refs)
            event_hash = hashlib.sha256(self._canonical(body).encode()).hexdigest()
            event = AuditEvent(**body, event_hash=event_hash)
            self._events.append(event)
            if self.path:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as f:
                    f.write(self._canonical(asdict(event)) + "\n")
            return event

    def verify_chain(self) -> bool:
        previous = "GENESIS"
        for event in self._events:
            data = asdict(event)
            actual = data.pop("event_hash")
            if data["previous_event_hash"] != previous:
                return False
            expected = hashlib.sha256(self._canonical(data).encode()).hexdigest()
            if expected != actual:
                return False
            previous = actual
        return True
