import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.experience_store import ExperienceStore

client = TestClient(app)

@pytest.fixture(autouse=True)
def isolate_test_store(tmp_path):
    test_store = ExperienceStore(storage_path=str(tmp_path / "test_experiences.json"))
    with patch("app.main.experience_store", test_store):
        yield

def test_api_health_endpoint():
    """Verify GET /api/health endpoint."""
    with patch("app.main.hindsight_service.health_check", return_value={"status": "connected", "bank_id": "ci-agent-development"}):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["active_bank"] in ("ci-agent-development", "ci-agent-demo")
        assert data["hindsight"]["status"] == "connected"

def test_api_record_experience_endpoint():
    """Verify POST /api/experience endpoint."""
    exp_payload = {
        "experience_id": "exp-api-001",
        "timestamp": "2026-09-29T00:00:00Z",
        "repository": "acme/api-test",
        "workflow": "test-ci",
        "failure_signature": "npm_install_timeout",
        "error_type": "TimeoutError",
        "error_message": "ETIMEDOUT",
        "environment": "node:18",
        "suspected_cause": "Network issue",
        "action_taken": "Retry",
        "action_result": "failure",
        "resolution": "Failed",
        "lesson_learned": "Do not retry"
    }

    with patch("app.main.hindsight_service.retain_experience", return_value={"success": True, "items_count": 1}):
        response = client.post("/api/experience", json=exp_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "recorded"
        assert data["experience"]["experience_id"] == "exp-api-001"
        assert data["hindsight_retain"]["success"] is True

def test_api_list_experiences_endpoint():
    """Verify GET /api/experiences endpoint."""
    response = client.get("/api/experiences")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_api_update_outcome_endpoint():
    """Verify POST /api/experiences/{id}/outcome endpoint."""
    # First ensure experience exists in store
    exp_payload = {
        "experience_id": "exp-api-update-001",
        "timestamp": "2026-09-29T00:00:00Z",
        "repository": "acme/api-test",
        "workflow": "test-ci",
        "failure_signature": "npm_install_timeout",
        "error_type": "TimeoutError",
        "error_message": "ETIMEDOUT",
        "environment": "node:18",
        "suspected_cause": "Network issue",
        "action_taken": "Pending action",
        "action_result": "failure",
        "resolution": "Unresolved",
        "lesson_learned": "Pending"
    }
    with patch("app.main.hindsight_service.retain_experience", return_value={"success": True}):
        client.post("/api/experience", json=exp_payload)

    outcome_payload = {
        "action_taken": "Updated action verified registry",
        "action_result": "success",
        "resolution": "Fixed successfully",
        "lesson_learned": "Verify registry"
    }
    with patch("app.main.hindsight_service.retain_experience", return_value={"success": True}):
        response = client.post("/api/experiences/exp-api-update-001/outcome", json=outcome_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "outcome_updated"
        assert data["experience"]["action_result"] == "success"
