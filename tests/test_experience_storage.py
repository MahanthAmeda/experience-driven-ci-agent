import pytest
import os
import shutil
from app.models import Experience, OutcomeUpdateRequest
from app.experience_store import ExperienceStore

@pytest.fixture
def temp_store(tmp_path):
    store_file = tmp_path / "test_experiences.json"
    return ExperienceStore(storage_path=str(store_file))

def test_experience_storage_and_outcome_update(temp_store):
    """E. Experience storage: action, outcome, resolution, lesson are stored correctly."""
    exp = Experience(
        experience_id="exp-test-001",
        timestamp="2026-09-29T00:00:00Z",
        repository="acme/test-repo",
        workflow="test-workflow",
        failure_signature="npm_install_timeout",
        error_type="TimeoutError",
        error_message="Connection timed out",
        environment="node:18",
        suspected_cause="Registry timeout",
        action_taken="Initial investigation",
        action_result="failure",
        resolution="No resolution yet",
        lesson_learned="Pending"
    )

    temp_store.add(exp)
    retrieved = temp_store.get("exp-test-001")
    assert retrieved is not None
    assert retrieved.action_taken == "Initial investigation"
    assert retrieved.action_result == "failure"

    # Update outcome
    update_req = OutcomeUpdateRequest(
        action_taken="Verified registry configuration",
        action_result="success",
        resolution="Switched mirror and build succeeded",
        lesson_learned="Always verify registry mirror"
    )

    updated = temp_store.update_outcome("exp-test-001", update_req)
    assert updated is not None
    assert updated.action_taken == "Verified registry configuration"
    assert updated.action_result == "success"
    assert updated.resolution == "Switched mirror and build succeeded"
    assert updated.lesson_learned == "Always verify registry mirror"
