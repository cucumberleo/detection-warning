import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import Body, Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .api_models import ChatRequest, DetectionRequest, EventRequest, LoginRequest, PreferenceUpdate
from .models import AlertRuleUpdate, GasType, Role, SessionPrincipal
from .platform import GasMonitorPlatform
from .storage import PlatformStore


ROOT = Path(__file__).resolve().parents[2]


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

    def current_principal(
        authorization: Annotated[str | None, Header()] = None,
    ) -> SessionPrincipal:
        token = authorization.removeprefix("Bearer ") if authorization else ""
        role_by_token: dict[str, Role] = {"demo-user": "user", "demo-admin": "admin"}
        role = role_by_token.get(token)
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="missing or invalid demo token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = platform.login(role)
        return SessionPrincipal(user_id=user["id"], role=role, device_ids=tuple(user["devices"]))

    Principal = Annotated[SessionPrincipal, Depends(current_principal)]

    def require_admin(principal: Principal) -> SessionPrincipal:
        if principal.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin access required")
        return principal

    AdminPrincipal = Annotated[SessionPrincipal, Depends(require_admin)]

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": app.version}

    @app.post("/api/demo/login")
    def login(payload: LoginRequest) -> dict[str, object]:
        return {
            "status": "success",
            "token": f"demo-{payload.role}",
            "user": platform.login(payload.role),
        }

    @app.get("/api/overview")
    def overview(principal: Principal) -> dict[str, object]:
        return {"status": "success", "data": platform.overview(principal)}

    @app.get("/api/devices")
    def visible_devices(principal: Principal) -> dict[str, object]:
        return {"status": "success", "data": platform.devices(principal)}

    @app.get("/api/detections")
    def detections(principal: Principal) -> dict[str, object]:
        return {"status": "success", "data": platform.detections(principal)}

    @app.post("/api/detections/simulate", status_code=status.HTTP_201_CREATED)
    def simulate(payload: DetectionRequest, principal: Principal) -> dict[str, object]:
        try:
            return {"status": "success", "data": platform.simulate(payload, principal)}
        except PermissionError as error:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error

    @app.get("/api/detections/export")
    def export_detections(principal: Principal) -> Response:
        return Response(
            platform.export_csv(principal),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=gas-detections.csv"},
        )

    @app.get("/api/alerts")
    def alerts(principal: Principal) -> dict[str, object]:
        return {"status": "success", "data": platform.alerts(principal)}

    @app.post("/api/alerts/{alert_id}/acknowledge")
    def acknowledge_alert(alert_id: str, principal: Principal) -> dict[str, object]:
        alert = platform.acknowledge_alert(alert_id, principal)
        if alert is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="alert not found")
        return {"status": "success", "data": alert}

    @app.get("/api/history/summary")
    @app.post("/api/llm/history_summary")
    def history_summary(principal: Principal) -> dict[str, object]:
        return {"status": "success", **platform.history_summary(principal)}

    @app.get("/api/preferences")
    def preferences(_principal: Principal) -> dict[str, object]:
        return {"status": "success", "data": platform.store.preferences()}

    @app.put("/api/preferences")
    def update_preferences(payload: PreferenceUpdate, _principal: Principal) -> dict[str, object]:
        updates = payload.model_dump(exclude_none=True)
        return {"status": "success", "data": platform.store.update_preferences(updates)}

    @app.post("/api/events", status_code=status.HTTP_202_ACCEPTED)
    def record_event(payload: EventRequest, principal: Principal) -> dict[str, str]:
        platform.store.record_event(
            {
                "name": payload.name,
                "page": payload.page,
                "role": principal.role,
                "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
        )
        return {"status": "success"}

    @app.get("/api/recommendations")
    def recommendations(principal: Principal) -> dict[str, object]:
        return {"status": "success", "data": platform.recommendations(principal)}

    @app.get("/api/admin/users")
    def users(_principal: AdminPrincipal) -> dict[str, object]:
        return {"status": "success", "data": platform.store.list_users()}

    @app.get("/api/admin/devices")
    def devices(_principal: AdminPrincipal) -> dict[str, object]:
        return {"status": "success", "data": platform.store.list_devices()}

    @app.get("/api/admin/alert-rules")
    def alert_rules(_principal: AdminPrincipal) -> dict[str, object]:
        return {"status": "success", "data": platform.store.alert_rules()}

    @app.put("/api/admin/alert-rules")
    def update_alert_rules(
        payload: Annotated[dict[GasType, AlertRuleUpdate], Body()],
        _principal: AdminPrincipal,
    ) -> dict[str, object]:
        rules = {gas: rule.model_dump() for gas, rule in payload.items()}
        return {"status": "success", "data": platform.store.update_alert_rules(rules)}

    @app.post("/api/agent/chat")
    def agent_chat(payload: ChatRequest, principal: Principal) -> dict[str, object]:
        return {"status": "success", "data": platform.chat(principal, payload.message)}

    return app


app = create_app()
