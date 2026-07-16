from __future__ import annotations

import csv
import io
import math
from collections import Counter
from datetime import datetime, timezone
from statistics import mean
from typing import Any
from uuid import uuid4

from .models import DetectionRequest, SessionPrincipal
from .storage import PlatformStore


class GasMonitorPlatform:
    """Domain interface for role-scoped monitoring workflows."""

    _concentrations = {
        "NH3": {"safe": 13.2, "warning": 26.4},
        "Toluene": {"safe": 7.8, "warning": 15.3},
        "HCHO": {"safe": 2.8, "warning": 7.2},
        "TEA": {"safe": 6.4, "warning": 18.6},
    }
    _responses = {"NH3": 0.418, "Toluene": 0.311, "HCHO": 0.246, "TEA": 0.386}

    def __init__(self, store: PlatformStore):
        self.store = store

    @staticmethod
    def _can_access(principal: SessionPrincipal, device_id: str) -> bool:
        return principal.role == "admin" or device_id in principal.device_ids

    def login(self, role: str) -> dict[str, Any]:
        return self.store.login_user(role)

    def devices(self, principal: SessionPrincipal) -> list[dict[str, Any]]:
        return [
            device
            for device in self.store.list_devices()
            if self._can_access(principal, device["id"])
        ]

    def simulate(
        self, request: DetectionRequest, principal: SessionPrincipal
    ) -> dict[str, Any]:
        device = next(
            (item for item in self.store.list_devices() if item["id"] == request.device_id),
            None,
        )
        if device is None:
            raise ValueError("device not found")
        if not self._can_access(principal, request.device_id):
            raise PermissionError("device is outside the current user's authorization scope")
        if device["status"] != "online":
            raise ValueError("device is offline")

        concentration = self._concentrations[request.gas_type][request.scenario]
        rule = self.store.alert_rules()[request.gas_type]
        state = "warning" if concentration >= rule["threshold"] else "safe"
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        detection_id = f"det-{uuid4().hex[:10]}"
        detection = {
            "id": detection_id,
            "device_id": request.device_id,
            "gas_type": request.gas_type,
            "concentration_ppm": concentration,
            "confidence": 0.91 if request.scenario == "warning" else 0.87,
            "response": self._responses[request.gas_type],
            "status": state,
            "algorithm_version": "baseline-web-v1",
            "processing_latency_ms": 164,
            "created_at": now,
            "curve": self._curve(request.gas_type, concentration),
        }
        self.store.insert_detection(detection)
        if state == "warning":
            self.store.insert_alert(
                {
                    "id": f"alt-{uuid4().hex[:10]}",
                    "detection_id": detection_id,
                    "gas_type": request.gas_type,
                    "device_id": request.device_id,
                    "concentration_ppm": concentration,
                    "status": "open",
                    "severity": rule["severity"],
                    "created_at": now,
                    "acknowledged_at": None,
                }
            )
        return detection

    @staticmethod
    def _curve(gas_type: str, concentration: float) -> dict[str, Any]:
        phase = {"NH3": 0.0, "Toluene": 0.8, "HCHO": 1.4, "TEA": 2.0}[gas_type]
        times = [round(index * 0.5, 1) for index in range(72)]
        amplitude = 0.34 + concentration / 85
        values = [
            round(
                1.1
                + math.sin(index / 5 + phase) * 0.045
                - amplitude * math.exp(-((index - 37) ** 2) / 145),
                4,
            )
            for index in range(72)
        ]
        return {"time": times, "values": values, "unit": "nA"}

    def detections(self, principal: SessionPrincipal) -> list[dict[str, Any]]:
        return [
            record
            for record in self.store.list_detections()
            if self._can_access(principal, record["device_id"])
        ]

    def alerts(self, principal: SessionPrincipal) -> list[dict[str, Any]]:
        return [
            alert
            for alert in self.store.list_alerts()
            if self._can_access(principal, alert["device_id"])
        ]

    def acknowledge_alert(
        self, alert_id: str, principal: SessionPrincipal
    ) -> dict[str, Any] | None:
        if not any(alert["id"] == alert_id for alert in self.alerts(principal)):
            return None
        return self.store.acknowledge_alert(
            alert_id, datetime.now(timezone.utc).isoformat(timespec="seconds")
        )

    def overview(self, principal: SessionPrincipal) -> dict[str, Any]:
        records = self.detections(principal)
        alerts = self.alerts(principal)
        devices = self.devices(principal)
        ppm = [float(record["concentration_ppm"]) for record in records]
        gas_counts = Counter(record["gas_type"] for record in records)
        trend_records = list(reversed(records[:7]))
        trend = [
            {"label": record["created_at"], "value": record["concentration_ppm"]}
            for record in trend_records
        ]
        return {
            "total_detections": len(records),
            "warning_count": sum(record["status"] == "warning" for record in records),
            "open_alert_count": sum(alert["status"] == "open" for alert in alerts),
            "online_devices": sum(device["status"] == "online" for device in devices),
            "total_devices": len(devices),
            "average_ppm": round(mean(ppm), 2) if ppm else 0,
            "peak_ppm": round(max(ppm), 2) if ppm else 0,
            "gas_counts": dict(gas_counts),
            "trend": trend,
        }

    def history_summary(self, principal: SessionPrincipal) -> dict[str, Any]:
        overview = self.overview(principal)
        if overview["total_detections"] == 0:
            summary = "暂无检测记录。完成一次监测后，这里会生成趋势与风险摘要。"
        else:
            summary = (
                f"当前范围共有 {overview['total_detections']} 条记录，平均浓度 "
                f"{overview['average_ppm']:.2f} ppm，峰值 {overview['peak_ppm']:.2f} ppm。"
                f"其中 {overview['warning_count']} 条触发预警，"
                f"仍有 {overview['open_alert_count']} 条待确认，建议优先复核最近的超限记录。"
            )
        return {"summary": summary, "source": "local", "stats": overview}

    def recommendations(self, principal: SessionPrincipal) -> list[dict[str, Any]]:
        stats = self.overview(principal)
        return [
            {
                "module": "alerts",
                "title": "处理待确认预警",
                "reason": f"当前有 {stats['open_alert_count']} 条待确认事件",
            },
            {
                "module": "monitor",
                "title": "运行一次复测",
                "reason": "通用处置建议：复测可验证峰值是否持续",
            },
            {
                "module": "analytics",
                "title": "查看浓度趋势",
                "reason": f"当前可见记录峰值为 {stats['peak_ppm']:.2f} ppm",
            },
        ]

    def chat(self, principal: SessionPrincipal, message: str) -> dict[str, Any]:
        stats = self.overview(principal)
        question = message.lower()
        if "预警" in question or "alert" in question:
            answer = f"当前有 {stats['open_alert_count']} 条待确认预警，建议先查看预警中心并核对最近一次检测曲线。"
            tools = ["get_alert_statistics"]
        elif "设备" in question or "device" in question:
            answer = f"当前授权范围内有 {stats['online_devices']} 台设备在线。"
            tools = ["get_device_status"]
        else:
            answer = f"最近可见记录的平均浓度为 {stats['average_ppm']:.2f} ppm，峰值为 {stats['peak_ppm']:.2f} ppm。"
            tools = ["get_concentration_trend"]
        return {"answer": answer, "tools": tools, "data_range": "当前身份授权范围内的持久化记录"}

    def export_csv(self, principal: SessionPrincipal) -> str:
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer)
        keys = (
            "id",
            "created_at",
            "device_id",
            "gas_type",
            "concentration_ppm",
            "confidence",
            "response",
            "status",
            "algorithm_version",
        )
        writer.writerow(keys)
        for record in self.detections(principal):
            writer.writerow([record[key] for key in keys])
        return buffer.getvalue()
