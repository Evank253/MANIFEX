"""Optional FastAPI adapter. Core CQS does not require FastAPI."""

from __future__ import annotations
from dataclasses import asdict
from .models import Capability, EvidenceRecord
from .service import CQSService

service = CQSService()

try:
    from fastapi import FastAPI, HTTPException
    app = FastAPI(title="CQS v0.1", version="0.1.0")

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "cqs", "version": "0.1.0"}

    @app.post("/capabilities")
    def register_capability(capability: Capability):
        try:
            return asdict(service.register_capability(capability))
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))

    @app.get("/capabilities/{capability_id}/{version}")
    def get_capability(capability_id: str, version: str):
        try:
            return asdict(service.capabilities[(capability_id, version)])
        except KeyError:
            raise HTTPException(status_code=404, detail="capability version not found")

    @app.post("/capabilities/{capability_id}/{version}/evidence")
    def append_evidence(capability_id: str, version: str, record: EvidenceRecord):
        if record.capability_id != capability_id or record.capability_version != version:
            raise HTTPException(status_code=400, detail="evidence capability identity mismatch")
        try:
            return asdict(service.append_evidence(record))
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc))

    @app.post("/capabilities/{capability_id}/{version}/qualify")
    def qualify(capability_id: str, version: str):
        try:
            return asdict(service.qualify(capability_id, version))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
except ImportError:
    app = None
