from __future__ import annotations

import json
import math
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


class PlatformStore:
    """Persistent adapter behind the platform's storage seam."""

    def __init__(self, database_path: str | Path):
        self.database_path = str(database_path)
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    device_ids TEXT NOT NULL,
                    status TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS devices (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    material TEXT NOT NULL,
                    location TEXT NOT NULL,
                    status TEXT NOT NULL,
                    signal_quality INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS alert_rules (
                    gas_type TEXT PRIMARY KEY,
                    threshold REAL NOT NULL,
                    severity TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS detections (
                    id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL REFERENCES devices(id),
                    gas_type TEXT NOT NULL,
                    concentration_ppm REAL NOT NULL,
                    confidence REAL NOT NULL,
                    response REAL NOT NULL,
                    status TEXT NOT NULL,
                    algorithm_version TEXT NOT NULL,
                    processing_latency_ms INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    curve_time TEXT NOT NULL,
                    curve_values TEXT NOT NULL,
                    curve_unit TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    detection_id TEXT NOT NULL REFERENCES detections(id),
                    gas_type TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    concentration_ppm REAL NOT NULL,
                    status TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    acknowledged_at TEXT
                );
                CREATE TABLE IF NOT EXISTS preferences (
                    owner_id TEXT PRIMARY KEY,
                    gas_types TEXT NOT NULL,
                    modules TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    page TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            connection.executemany(
                "INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?, ?)",
                [
                    ("u-001", "张同学", "user", '["dev-01"]', "active"),
                    ("u-002", "李同学", "user", '["dev-01", "dev-02"]', "active"),
                    ("admin-001", "平台管理员", "admin", '["dev-01", "dev-02", "dev-03"]', "active"),
                ],
            )
            connection.executemany(
                "INSERT OR IGNORE INTO devices VALUES (?, ?, ?, ?, ?, ?)",
                [
                    ("dev-01", "ZnO-200-A", "N,P-CDs/ZnO", "实验室 A", "online", 96),
                    ("dev-02", "ZnO-200-B", "N-CDs/ZnO", "实验室 B", "online", 89),
                    ("dev-03", "ZnO-400-C", "P-CDs/ZnO", "材料室", "offline", 0),
                ],
            )
            connection.executemany(
                "INSERT OR IGNORE INTO alert_rules VALUES (?, ?, ?)",
                [
                    ("NH3", 20.0, "medium"),
                    ("Toluene", 10.0, "high"),
                    ("HCHO", 5.0, "high"),
                    ("TEA", 10.0, "medium"),
                ],
            )
            connection.execute(
                "INSERT OR IGNORE INTO preferences VALUES (?, ?, ?)",
                ("u-001", '["NH3"]', '["monitor", "alerts", "analytics"]'),
            )
            count = connection.execute("SELECT COUNT(*) FROM detections").fetchone()[0]
            if count == 0:
                self._seed_detections(connection)

    def _seed_detections(self, connection: sqlite3.Connection) -> None:
        now = datetime.now(timezone.utc)
        seeds = [
            ("det-006", "dev-01", "NH3", 26.4, 0.91, 0.418, "warning", 32),
            ("det-005", "dev-02", "Toluene", 7.8, 0.88, 0.231, "safe", 96),
            ("det-004", "dev-01", "NH3", 13.2, 0.84, 0.267, "safe", 180),
            ("det-003", "dev-03", "Toluene", 15.3, 0.79, 0.362, "warning", 1440),
        ]
        for detection_id, device_id, gas, ppm, confidence, response, state, minutes in seeds:
            created_at = (now - timedelta(minutes=minutes)).isoformat(timespec="seconds")
            curve_time, curve_values = self._seed_curve(ppm)
            connection.execute(
                "INSERT INTO detections VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    detection_id, device_id, gas, ppm, confidence, response, state,
                    "baseline-web-v1", 164, created_at,
                    json.dumps(curve_time), json.dumps(curve_values), "nA",
                ),
            )
            if state == "warning":
                severity = "high" if gas == "Toluene" else "medium"
                alert_state = "acknowledged" if detection_id == "det-003" else "open"
                connection.execute(
                    "INSERT INTO alerts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        detection_id.replace("det", "alt"), detection_id, gas,
                        device_id, ppm, alert_state, severity, created_at,
                        created_at if alert_state == "acknowledged" else None,
                    ),
                )

    @staticmethod
    def _seed_curve(ppm: float) -> tuple[list[float], list[float]]:
        times = [round(index * 0.5, 1) for index in range(48)]
        values = [
            round(1.08 + math.sin(index / 4) * 0.035 - (ppm / 90) * math.exp(-((index - 25) ** 2) / 95), 4)
            for index in range(48)
        ]
        return times, values

    def list_users(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM users ORDER BY role, id").fetchall()
        return [dict(row) | {"devices": json.loads(row["device_ids"])} for row in rows]

    def login_user(self, role: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM users WHERE role = ? ORDER BY id LIMIT 1", (role,)
            ).fetchone()
        if row is None:
            raise LookupError(role)
        result = dict(row)
        result["devices"] = json.loads(result.pop("device_ids"))
        return result

    def list_devices(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM devices ORDER BY id").fetchall()
        return [dict(row) for row in rows]

    def device_exists(self, device_id: str) -> bool:
        with self._connect() as connection:
            return connection.execute("SELECT 1 FROM devices WHERE id = ?", (device_id,)).fetchone() is not None

    def alert_rules(self) -> dict[str, dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM alert_rules ORDER BY gas_type").fetchall()
        return {
            row["gas_type"]: {"threshold": row["threshold"], "severity": row["severity"]}
            for row in rows
        }

    def update_alert_rules(self, rules: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        with self._connect() as connection:
            connection.executemany(
                "UPDATE alert_rules SET threshold = ?, severity = ? WHERE gas_type = ?",
                [(rule["threshold"], rule["severity"], gas) for gas, rule in rules.items()],
            )
        return self.alert_rules()

    def insert_detection(self, detection: dict[str, Any]) -> None:
        curve = detection["curve"]
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO detections VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    detection["id"], detection["device_id"], detection["gas_type"],
                    detection["concentration_ppm"], detection["confidence"],
                    detection["response"], detection["status"],
                    detection["algorithm_version"], detection["processing_latency_ms"],
                    detection["created_at"], json.dumps(curve["time"]),
                    json.dumps(curve["values"]), curve["unit"],
                ),
            )

    def insert_alert(self, alert: dict[str, Any]) -> None:
        keys = (
            "id", "detection_id", "gas_type", "device_id", "concentration_ppm",
            "status", "severity", "created_at", "acknowledged_at",
        )
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO alerts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                tuple(alert[key] for key in keys),
            )

    def list_detections(self, device_id: str | None = None) -> list[dict[str, Any]]:
        return [self._detection_from_row(row) for row in self._rows("detections", device_id)]

    def list_alerts(self, device_id: str | None = None) -> list[dict[str, Any]]:
        return [dict(row) for row in self._rows("alerts", device_id)]

    def _rows(self, table: str, device_id: str | None) -> Iterable[sqlite3.Row]:
        query = f"SELECT * FROM {table}"
        params: tuple[Any, ...] = ()
        if device_id:
            query += " WHERE device_id = ?"
            params = (device_id,)
        query += " ORDER BY created_at DESC, id DESC"
        with self._connect() as connection:
            return connection.execute(query, params).fetchall()

    @staticmethod
    def _detection_from_row(row: sqlite3.Row) -> dict[str, Any]:
        record = dict(row)
        record["curve"] = {
            "time": json.loads(record.pop("curve_time")),
            "values": json.loads(record.pop("curve_values")),
            "unit": record.pop("curve_unit"),
        }
        return record

    def acknowledge_alert(self, alert_id: str, acknowledged_at: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE alerts SET status = 'acknowledged', acknowledged_at = ? WHERE id = ?",
                (acknowledged_at, alert_id),
            )
            if cursor.rowcount == 0:
                return None
            row = connection.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
        return dict(row) if row else None

    def preferences(self) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM preferences WHERE owner_id = 'u-001'").fetchone()
        return {"gas_types": json.loads(row["gas_types"]), "modules": json.loads(row["modules"])}

    def update_preferences(self, updates: dict[str, Any]) -> dict[str, Any]:
        current = self.preferences() | updates
        with self._connect() as connection:
            connection.execute(
                "UPDATE preferences SET gas_types = ?, modules = ? WHERE owner_id = 'u-001'",
                (json.dumps(current["gas_types"]), json.dumps(current["modules"])),
            )
        return current

    def record_event(self, event: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO events (name, page, role, created_at) VALUES (?, ?, ?, ?)",
                (event["name"], event["page"], event["role"], event["created_at"]),
            )
