from fastapi.testclient import TestClient

from backend.app.application import create_app


def make_client(tmp_path):
    return TestClient(create_app(database_path=tmp_path / "platform-test.db"))


def test_admin_threshold_update_changes_the_alert_decision(tmp_path):
    client = make_client(tmp_path)
    update = client.put(
        "/api/admin/alert-rules",
        json={"Toluene": {"threshold": 5.0, "severity": "high"}},
    )
    detection = client.post(
        "/api/detections/simulate",
        json={"device_id": "dev-01", "gas_type": "Toluene", "scenario": "safe"},
    )
    assert update.status_code == 200
    assert update.json()["data"]["Toluene"]["threshold"] == 5.0
    assert detection.status_code == 201
    assert detection.json()["data"]["status"] == "warning"


def test_role_scope_limits_user_history_to_authorized_device(tmp_path):
    client = make_client(tmp_path)
    client.post(
        "/api/detections/simulate",
        json={"device_id": "dev-02", "gas_type": "NH3", "scenario": "warning"},
    )
    user_records = client.get("/api/detections", params={"role": "user"}).json()["data"]
    admin_records = client.get("/api/detections", params={"role": "admin"}).json()["data"]
    assert all(record["device_id"] == "dev-01" for record in user_records)
    assert any(record["device_id"] == "dev-02" for record in admin_records)


def test_alert_can_be_acknowledged_through_public_interface(tmp_path):
    client = make_client(tmp_path)
    detection = client.post(
        "/api/detections/simulate",
        json={"device_id": "dev-01", "gas_type": "NH3", "scenario": "warning"},
    ).json()["data"]
    alert = next(
        item
        for item in client.get("/api/alerts").json()["data"]
        if item["detection_id"] == detection["id"]
    )
    result = client.post(f"/api/alerts/{alert['id']}/acknowledge")
    assert result.status_code == 200
    assert result.json()["data"]["status"] == "acknowledged"
    assert result.json()["data"]["acknowledged_at"]


def test_csv_export_contains_only_visible_records(tmp_path):
    client = make_client(tmp_path)
    client.post(
        "/api/detections/simulate",
        json={"device_id": "dev-02", "gas_type": "TEA", "scenario": "safe"},
    )
    response = client.get("/api/detections/export", params={"role": "user"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "gas_type" in response.text
    assert "dev-02" not in response.text


def test_invalid_detection_payload_is_rejected(tmp_path):
    client = make_client(tmp_path)
    response = client.post(
        "/api/detections/simulate",
        json={"device_id": "dev-01", "gas_type": "Unknown", "scenario": "safe"},
    )
    assert response.status_code == 422
