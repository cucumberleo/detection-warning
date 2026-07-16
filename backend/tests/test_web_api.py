from fastapi.testclient import TestClient

from backend.app.application import create_app


def make_client(tmp_path):
    return TestClient(create_app(database_path=tmp_path / "platform-test.db"))


def auth(role: str = "user") -> dict[str, str]:
    return {"Authorization": f"Bearer demo-{role}"}


def test_protected_routes_require_a_server_validated_token(tmp_path):
    client = make_client(tmp_path)
    assert client.get("/api/overview").status_code == 401
    assert client.get("/api/overview", headers=auth()).status_code == 200


def test_user_cannot_escalate_with_a_query_parameter_or_admin_route(tmp_path):
    client = make_client(tmp_path)
    overview = client.get("/api/overview?role=admin", headers=auth("user"))
    forbidden = client.get("/api/admin/users", headers=auth("user"))
    assert overview.status_code == 200
    assert overview.json()["data"]["total_devices"] == 1
    assert forbidden.status_code == 403


def test_admin_threshold_update_changes_the_alert_decision(tmp_path):
    client = make_client(tmp_path)
    update = client.put(
        "/api/admin/alert-rules",
        json={"Toluene": {"threshold": 5.0, "severity": "high"}},
        headers=auth("admin"),
    )
    detection = client.post(
        "/api/detections/simulate",
        json={"device_id": "dev-01", "gas_type": "Toluene", "scenario": "safe"},
        headers=auth("admin"),
    )
    assert update.status_code == 200
    assert update.json()["data"]["Toluene"]["threshold"] == 5.0
    assert detection.status_code == 201
    assert detection.json()["data"]["status"] == "warning"


def test_user_scope_limits_devices_history_and_detection_control(tmp_path):
    client = make_client(tmp_path)
    client.post(
        "/api/detections/simulate",
        json={"device_id": "dev-02", "gas_type": "NH3", "scenario": "warning"},
        headers=auth("admin"),
    )
    user_devices = client.get("/api/devices", headers=auth("user")).json()["data"]
    user_records = client.get("/api/detections", headers=auth("user")).json()["data"]
    denied = client.post(
        "/api/detections/simulate",
        json={"device_id": "dev-02", "gas_type": "NH3", "scenario": "safe"},
        headers=auth("user"),
    )
    assert [device["id"] for device in user_devices] == ["dev-01"]
    assert all(record["device_id"] == "dev-01" for record in user_records)
    assert denied.status_code == 403


def test_alert_acknowledgement_is_limited_to_visible_scope(tmp_path):
    client = make_client(tmp_path)
    detection = client.post(
        "/api/detections/simulate",
        json={"device_id": "dev-02", "gas_type": "NH3", "scenario": "warning"},
        headers=auth("admin"),
    ).json()["data"]
    alert = next(
        item
        for item in client.get("/api/alerts", headers=auth("admin")).json()["data"]
        if item["detection_id"] == detection["id"]
    )
    denied = client.post(
        f"/api/alerts/{alert['id']}/acknowledge", headers=auth("user")
    )
    accepted = client.post(
        f"/api/alerts/{alert['id']}/acknowledge", headers=auth("admin")
    )
    assert denied.status_code == 404
    assert accepted.status_code == 200
    assert accepted.json()["data"]["status"] == "acknowledged"


def test_csv_export_contains_only_visible_records(tmp_path):
    client = make_client(tmp_path)
    client.post(
        "/api/detections/simulate",
        json={"device_id": "dev-02", "gas_type": "TEA", "scenario": "safe"},
        headers=auth("admin"),
    )
    response = client.get("/api/detections/export", headers=auth("user"))
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "gas_type" in response.text
    assert "dev-02" not in response.text


def test_invalid_detection_payload_is_rejected(tmp_path):
    client = make_client(tmp_path)
    response = client.post(
        "/api/detections/simulate",
        json={"device_id": "dev-01", "gas_type": "Unknown", "scenario": "safe"},
        headers=auth("user"),
    )
    assert response.status_code == 422
