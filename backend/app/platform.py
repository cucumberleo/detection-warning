from __future__ import annotations

import csv
import io
import math
from collections import Counter
from datetime import datetime, timezone
from statistics import mean
from typing import Any
from uuid import uuid4

from .models import DetectionRequest
from .storage import PlatformStore


class GasMonitorPlatform:
    """Deep domain module for the complete web monitoring workflow."""

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
    def visible_device(role: str) -> str | None:
        return None if role == "admin" else "dev-01"

    def login(self, role: str) -> dict[str, Any]:
        return self.store.login_user(role)

    def simulate(self, request: DetectionRequest) -> dict[str, Any]:
        if not self.store.device_exists(request.device_id):
            raise ValueError("device not found")
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
            round(1.1 + math.sin(index / 5 + phase) * 0.045 - amplitude * math.exp(-((index - 37) ** 2) / 145), 4)
            for index in range(72)
        ]
        return {"time": times, "values": values, "unit": "nA"}

    def detections(self, role: str) -> list[dict[str, Any]]:
        return self.store.list_detections(self.visible_device(role))

    def alerts(self, role: str) -> list[dict[str, Any]]:
        return self.store.list_alerts(self.visible_device(role))

    def overview(self, role: str) -> dict[str, Any]:
        records = self.detections(role)
        alerts = self.alerts(role)
        devices = self.store.list_devices()
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
            "average_ppm": round(mean(ppm), 2) if ppm else 0,
            "peak_ppm": round(max(ppm), 2) if ppm else 0,
            "gas_counts": dict(gas_counts),
            "trend": trend,
        }

    def history_summary(self, role: str) -> dict[str, Any]:
        overview = self.overview(role)
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

    def recommendations(self, role: str) -> list[dict[str, Any]]:
        stats = self.overview(role)
        return [
            {"module": "alerts", "title": "处理待确认预警", "reason": f"当前有 {stats['open_alert_count']} 条待确认事件", "score": 0.94},
            {"module": "monitor", "title": "运行一次复测", "reason": "复测可验证峰值是否持续", "score": 0.86},
            {"module": "analytics", "title": "查看浓度趋势", "reason": f"当前峰值为 {stats['peak_ppm']:.2f} ppm", "score": 0.78},
        ]

    def chat(self, role: str, message: str) -> dict[str, Any]:
        stats = self.overview(role)
        question = message.lower()
        if "预警" in question or "alert" in question:
            answer = f"当前有 {stats['open_alert_count']} 条待确认预警，建议先查看预警中心并核对最近一次检测曲线。"
            tools = ["get_alert_statistics"]
        elif "设备" in question or "device" in question:
            answer = f"当前 {stats['online_devices']} 台设备在线。离线设备不会进入实时监测候选列表。"
            tools = ["get_device_status"]
        else:
            answer = f"最近可见记录的平均浓度为 {stats['average_ppm']:.2f} ppm，峰值为 {stats['peak_ppm']:.2f} ppm。"
            tools = ["get_concentration_trend"]
        return {"answer": answer, "tools": tools, "data_range": "当前可见的持久化记录"}

    def export_csv(self, role: str) -> str:
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer)
        writer.writerow(["id", "created_at", "device_id", "gas_type", "concentration_ppm", "confidence", "response", "status", "algorithm_version"])
        for record in self.detections(role):
            writer.writerow([record[key] for key in ("id", "created_at", "device_id", "gas_type", "concentration_ppm", "confidence", "response", "status", "algorithm_version")])
        return buffer.getvalue()
