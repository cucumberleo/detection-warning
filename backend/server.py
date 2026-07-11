"""Gas Monitor Web Demo backend.

This is intentionally a small, dependency-light collaboration baseline.  It
contains only demonstration data in memory; replace each endpoint's mock
implementation with the team's database/service layer in later sprints.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"
app = Flask(__name__, static_folder=None)

ALERT_RULES = {
    "NH3": {"threshold": 20.0, "severity": "medium"},
    "Toluene": {"threshold": 10.0, "severity": "high"},
}

USERS = [
    {"id": "u-001", "name": "张同学", "role": "user", "devices": ["dev-01"]},
    {"id": "u-002", "name": "李同学", "role": "user", "devices": ["dev-01", "dev-02"]},
    {"id": "admin-001", "name": "管理员", "role": "admin", "devices": ["dev-01", "dev-02", "dev-03"]},
]

DEVICES = [
    {"id": "dev-01", "name": "ZnO-200-A", "material": "N,P-CDs/ZnO", "location": "实验室 A", "status": "online"},
    {"id": "dev-02", "name": "ZnO-200-B", "material": "N-CDs/ZnO", "location": "实验室 B", "status": "online"},
    {"id": "dev-03", "name": "ZnO-400-C", "material": "P-CDs/ZnO", "location": "材料室", "status": "offline"},
]


def iso_at(minutes_ago: int) -> str:
    return (datetime.now() - timedelta(minutes=minutes_ago)).isoformat(timespec="seconds")


DETECTIONS: list[dict[str, Any]] = [
    {"id": "det-006", "device_id": "dev-01", "gas_type": "NH3", "concentration_ppm": 26.4, "confidence": 0.91, "response": 0.418, "status": "warning", "algorithm_version": "baseline-v0", "created_at": iso_at(32)},
    {"id": "det-005", "device_id": "dev-02", "gas_type": "Toluene", "concentration_ppm": 7.8, "confidence": 0.88, "response": 0.231, "status": "safe", "algorithm_version": "baseline-v0", "created_at": iso_at(96)},
    {"id": "det-004", "device_id": "dev-01", "gas_type": "NH3", "concentration_ppm": 13.2, "confidence": 0.84, "response": 0.267, "status": "safe", "algorithm_version": "baseline-v0", "created_at": iso_at(180)},
    {"id": "det-003", "device_id": "dev-03", "gas_type": "Toluene", "concentration_ppm": 15.3, "confidence": 0.79, "response": 0.362, "status": "warning", "algorithm_version": "baseline-v0", "created_at": iso_at(1440)},
]

ALERTS: list[dict[str, Any]] = [
    {"id": "alt-002", "detection_id": "det-006", "gas_type": "NH3", "device_id": "dev-01", "concentration_ppm": 26.4, "status": "open", "severity": "medium", "created_at": iso_at(32)},
    {"id": "alt-001", "detection_id": "det-003", "gas_type": "Toluene", "device_id": "dev-03", "concentration_ppm": 15.3, "status": "acknowledged", "severity": "high", "created_at": iso_at(1440)},
]

PREFERENCES = {"gas_types": ["NH3"], "modules": ["monitor", "alerts", "analytics"]}
EVENTS: list[dict[str, Any]] = []


def visible_detections(role: str) -> list[dict[str, Any]]:
    if role == "admin":
        return DETECTIONS
    return [item for item in DETECTIONS if item["device_id"] == "dev-01"]


def overview(role: str) -> dict[str, Any]:
    records = visible_detections(role)
    alerts = ALERTS if role == "admin" else [a for a in ALERTS if a["device_id"] == "dev-01"]
    return {
        "total_detections": len(records),
        "warning_count": len([r for r in records if r["status"] == "warning"]),
        "open_alert_count": len([a for a in alerts if a["status"] == "open"]),
        "online_devices": len([d for d in DEVICES if d["status"] == "online"]),
        "gas_counts": {
            gas: len([r for r in records if r["gas_type"] == gas])
            for gas in ("NH3", "Toluene")
        },
        "trend": [12, 18, 14, 21, 17, 26, 20],
    }


@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/assets/<path:filename>")
def assets(filename: str):
    return send_from_directory(FRONTEND_DIR, filename)


@app.post("/api/demo/login")
def login():
    payload = request.get_json(silent=True) or {}
    role = payload.get("role", "user")
    user = next((u for u in USERS if u["role"] == role), USERS[0])
    return jsonify({"status": "success", "token": f"demo-{role}", "user": user})


@app.get("/api/overview")
def get_overview():
    return jsonify({"status": "success", "data": overview(request.args.get("role", "user"))})


@app.get("/api/detections")
def get_detections():
    role = request.args.get("role", "user")
    return jsonify({"status": "success", "data": visible_detections(role)})


@app.post("/api/detections/simulate")
def simulate_detection():
    payload = request.get_json(silent=True) or {}
    gas = payload.get("gas_type", "NH3")
    device_id = payload.get("device_id", "dev-01")
    concentration = 26.4 if gas == "NH3" else 12.6
    rule = ALERT_RULES[gas]
    status = "warning" if concentration >= rule["threshold"] else "safe"
    detection = {
        "id": f"det-{len(DETECTIONS) + 1:03}", "device_id": device_id,
        "gas_type": gas, "concentration_ppm": concentration,
        "confidence": 0.89, "response": 0.418 if gas == "NH3" else 0.311,
        "status": status, "algorithm_version": "baseline-v0", "created_at": iso_at(0),
        "curve": [round(0.16 + (i / 75) * 0.24 + (0.025 if i % 9 < 4 else -0.01), 3) for i in range(48)],
    }
    DETECTIONS.insert(0, detection)
    if status == "warning":
        ALERTS.insert(0, {
            "id": f"alt-{len(ALERTS) + 1:03}", "detection_id": detection["id"],
            "gas_type": gas, "device_id": device_id,
            "concentration_ppm": concentration, "status": "open",
            "severity": rule["severity"], "created_at": detection["created_at"],
        })
    return jsonify({"status": "success", "data": detection})


@app.get("/api/alerts")
def get_alerts():
    role = request.args.get("role", "user")
    data = ALERTS if role == "admin" else [a for a in ALERTS if a["device_id"] == "dev-01"]
    return jsonify({"status": "success", "data": data})


@app.post("/api/alerts/<alert_id>/acknowledge")
def acknowledge_alert(alert_id: str):
    alert = next((a for a in ALERTS if a["id"] == alert_id), None)
    if alert is None:
        return jsonify({"error": "alert not found"}), 404
    alert["status"] = "acknowledged"
    return jsonify({"status": "success", "data": alert})


@app.get("/api/preferences")
def get_preferences():
    return jsonify({"status": "success", "data": PREFERENCES})


@app.put("/api/preferences")
def update_preferences():
    payload = request.get_json(silent=True) or {}
    PREFERENCES.update({key: value for key, value in payload.items() if key in PREFERENCES})
    return jsonify({"status": "success", "data": PREFERENCES})


@app.post("/api/events")
def record_event():
    event = request.get_json(silent=True) or {}
    event["created_at"] = iso_at(0)
    EVENTS.append(event)
    return jsonify({"status": "success"})


@app.get("/api/recommendations")
def recommendations():
    return jsonify({"status": "success", "data": [
        {"module": "alerts", "title": "预警中心", "reason": "你关注 NH3，且有 1 条待确认预警", "score": 0.93},
        {"module": "monitor", "title": "实时监测", "reason": "你最近多次查看 ZnO-200-A", "score": 0.82},
        {"module": "analytics", "title": "浓度趋势", "reason": "根据近期访问行为推荐", "score": 0.71},
    ]})


@app.get("/api/admin/users")
def admin_users():
    return jsonify({"status": "success", "data": USERS})


@app.get("/api/admin/devices")
def admin_devices():
    return jsonify({"status": "success", "data": DEVICES})


@app.route("/api/admin/alert-rules", methods=["GET", "PUT"])
def admin_alert_rules():
    if request.method == "PUT":
        payload = request.get_json(silent=True) or {}
        for gas, config in payload.items():
            if gas in ALERT_RULES and isinstance(config, dict):
                ALERT_RULES[gas].update(config)
    return jsonify({"status": "success", "data": ALERT_RULES})


@app.post("/api/agent/chat")
def agent_chat():
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("message", "")).lower()
    role = payload.get("role", "user")
    stats = overview(role)
    if "预警" in question:
        answer = f"当前可见范围内有 {stats['open_alert_count']} 条待确认预警；最近一条为 NH3，浓度 26.4 ppm。"
        tools = ["get_alert_statistics"]
    elif "趋势" in question or "浓度" in question:
        answer = "最近 7 个统计时段的浓度指标总体波动上升，峰值出现在第 6 个时段。建议继续观察并复测。"
        tools = ["get_concentration_trend"]
    elif "设备" in question:
        answer = f"当前共有 {stats['online_devices']} 台在线设备。ZnO-200-A 最近一次检测为 NH3 26.4 ppm。"
        tools = ["get_device_status"]
    else:
        answer = f"在当前数据范围内，共有 {stats['total_detections']} 条检测记录，其中 {stats['warning_count']} 条触发预警。你可以继续询问预警、趋势或设备状态。"
        tools = ["get_gas_statistics"]
    return jsonify({"status": "success", "data": {"answer": answer, "tools": tools, "data_range": "Demo 最近 7 天"}})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
