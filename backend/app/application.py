from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Body, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .api_models import ChatRequest, DetectionRequest, EventRequest, LoginRequest, PreferenceUpdate
from .models import AlertRuleUpdate, GasType
from .platform import GasMonitorPlatform
from .storage import PlatformStore


ROOT = Path(__file__).resolve().parents[2]
Role = Literal["user", "admin"]


def create_app(database_path: str | Path | None = None) -> FastAPI:
    database = database_path or os.environ.get("GAS_MONITOR_DB") or ROOT / "data" / "gas_monitor.db"
    platform = GasMonitorPlatform(PlatformStore(database))
    app = FastAPI(
        title="Gas Sense Platform API",
        version="1.0.0",
        description="Photovoltaic self-powered gas sensor monitoring platform.",
    )
    app.state.platform = platform
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": app.version}

    @app.post("/api/demo/login")
    def login(payload: LoginRequest) -> dict[str, object]:
        return {"status": "success", "token": f"demo-{payload.role}", "user": platform.login(payload.role)}

    @app.get("/api/overview")
    def overview(role: Role = "user") -> dict[str, object]:
        return {"status": "success", "data": platform.overview(role)}

    @app.get("/api/detections")
    def detections(role: Role = "user") -> dict[str, object]:
        return {"status": "success", "data": platform.detections(role)}

    @app.post("/api/detections/simulate", status_code=status.HTTP_201_CREATED)
    def simulate(payload: DetectionRequest) -> dict[str, object]:
        try:
            return {"status": "success", "data": platform.simulate(payload)}
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.get("/api/detections/export")
    def export_detections(role: Role = "user") -> Response:
        return Response(
            platform.export_csv(role),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=gas-detections.csv"},
        )

    @app.get("/api/alerts")
    def alerts(role: Role = "user") -> dict[str, object]:
        return {"status": "success", "data": platform.alerts(role)}

    @app.post("/api/alerts/{alert_id}/acknowledge")
    def acknowledge_alert(alert_id: str) -> dict[str, object]:
        alert = platform.store.acknowledge_alert(
            alert_id, datetime.now(timezone.utc).isoformat(timespec="seconds")
        )
        if alert is None:
            raise HTTPException(status_code=404, detail="alert not found")
        return {"status": "success", "data": alert}

    @app.get("/api/history/summary")
    @app.post("/api/llm/history_summary")
    def history_summary(
        role: Role = "user",
        payload: Annotated[dict[str, object] | None, Body()] = None,
    ) -> dict[str, object]:
        requested_role = payload.get("role", role) if payload else role
        safe_role: Role = "admin" if requested_role == "admin" else "user"
        return {"status": "success", **platform.history_summary(safe_role)}

    @app.get("/api/preferences")
    def preferences() -> dict[str, object]:
        return {"status": "success", "data": platform.store.preferences()}

    @app.put("/api/preferences")
    def update_preferences(payload: PreferenceUpdate) -> dict[str, object]:
        updates = payload.model_dump(exclude_none=True)
        return {"status": "success", "data": platform.store.update_preferences(updates)}

    @app.post("/api/events", status_code=status.HTTP_202_ACCEPTED)
    def record_event(payload: EventRequest) -> dict[str, str]:
        platform.store.record_event(payload.model_dump() | {"created_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
        return {"status": "success"}

    @app.get("/api/recommendations")
    def recommendations(role: Role = "user") -> dict[str, object]:
        return {"status": "success", "data": platform.recommendations(role)}

    @app.get("/api/admin/users")
    def users() -> dict[str, object]:
        return {"status": "success", "data": platform.store.list_users()}

    @app.get("/api/admin/devices")
    def devices() -> dict[str, object]:
        return {"status": "success", "data": platform.store.list_devices()}

    @app.get("/api/admin/alert-rules")
    def alert_rules() -> dict[str, object]:
        return {"status": "success", "data": platform.store.alert_rules()}

    @app.put("/api/admin/alert-rules")
    def update_alert_rules(
        payload: Annotated[dict[GasType, AlertRuleUpdate], Body()],
    ) -> dict[str, object]:
        rules = {gas: rule.model_dump() for gas, rule in payload.items()}
        return {"status": "success", "data": platform.store.update_alert_rules(rules)}

    @app.post("/api/agent/chat")
    def agent_chat(payload: ChatRequest) -> dict[str, object]:
        return {"status": "success", "data": platform.chat(payload.role, payload.message)}

    return app


app = create_app()
