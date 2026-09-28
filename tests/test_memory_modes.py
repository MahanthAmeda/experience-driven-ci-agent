import pytest
from unittest.mock import MagicMock, patch
from app.models import FailureInfo, AnalyseRequest
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

@pytest.fixture
def sample_npm_failure():
    return {
        "repository": "acme/web-frontend",
        "workflow": "ci-pipeline",
        "failure_signature": "npm_install_timeout",
        "error_type": "FetchError",
        "error_message": "ETIMEDOUT: network connection timed out trying to reach registry.npmjs.org",
        "environment": "node:18 / ubuntu-latest",
        "suspected_cause": "Network latency or registry unreachable"
    }

def test_memory_off_does_not_call_recall(sample_npm_failure):
    """A. When memory is OFF, Hindsight recall() must NOT be called and baseline is returned."""
    with patch("app.main.hindsight_service.recall_memories") as mock_recall:
        response = client.post(
            "/api/analyse",
            json={
                "failure": sample_npm_failure,
                "memory_enabled": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify recall was NOT called
        mock_recall.assert_not_called()
        
        # Verify baseline recommendation
        assert data["memory_enabled"] is False
        assert "Retry the npm installation once" in data["recommendation"]
        assert "Memory is OFF" in data["reasoning"]
        assert data["recalled_experiences"] == []
        assert data["influencing_experiences"] == []

def test_memory_on_calls_recall(sample_npm_failure):
    """B. When memory is ON, Hindsight recall() MUST be called and results evaluated."""
    mock_memory = MagicMock()
    mock_memory.text = "CI Failure [exp-1]: npm_install_timeout. Action: Retry npm install. Result: failure."
    mock_memory.type = "experience"
    mock_memory.id = "mem-1"
    mock_memory.metadata = {"failure_signature": "npm_install_timeout", "action_result": "failure"}
    mock_memory.tags = ["npm_install_timeout", "result:failure"]

    with patch("app.main.hindsight_service.recall_memories", return_value=[mock_memory]) as mock_recall:
        response = client.post(
            "/api/analyse",
            json={
                "failure": sample_npm_failure,
                "memory_enabled": True
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Verify recall WAS called
        mock_recall.assert_called_once()
        assert data["memory_enabled"] is True
        assert len(data["recalled_experiences"]) == 1
        assert len(data["relevant_experiences"]) == 1
