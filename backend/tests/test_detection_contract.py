import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.application import create_app


CONTRACT = Path(__file__).resolve().parents[2] / "contracts" / "detection-result.json"


def test_simulated_detection_matches_the_canonical_contract(tmp_path):
    schema = json.loads(CONTRACT.read_text(encoding="utf-8"))
    client = TestClient(create_app(database_path=tmp_path / "contract-test.db"))
    response = client.post(
        "/api/detections/simulate",
        json={"device_id": "dev-01", "gas_type": "NH3", "scenario": "safe"},
        headers={"Authorization": "Bearer demo-user"},
    )
    result = response.json()["data"]

    assert response.status_code == 201
    assert set(schema["required"]).issubset(result)
    assert result["gas_type"] in schema["properties"]["gas_type"]["enum"]
    assert result["status"] in schema["properties"]["status"]["enum"]
    assert 0 <= result["confidence"] <= 1
    assert len(result["curve"]["time"]) == len(result["curve"]["values"])
    assert result["curve"]["unit"] == schema["properties"]["curve"]["properties"]["unit"]["const"]
