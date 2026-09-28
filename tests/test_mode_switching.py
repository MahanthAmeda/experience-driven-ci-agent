import os
import pytest
from unittest.mock import patch, MagicMock
from app.config import get_config_for_mode, HINDSIGHT_DEV_BANK_ID, HINDSIGHT_DEMO_BANK_ID
from app.hindsight_service import HindsightService
from app.experience_store import ExperienceStore
from app.models import Experience

def test_development_mode_configuration():
    """Verify development mode resolves ci-agent-development, dev key, and dev store."""
    bank, key, store_path, forbidden = get_config_for_mode("development")
    assert bank == "ci-agent-development"
    assert store_path == os.path.join("data", "experiences.json")
    assert "ci-agent-demo" in forbidden
    assert "ci-agent-development" not in forbidden

def test_demo_mode_configuration():
    """Verify demo mode resolves ci-agent-demo, demo key, and demo store."""
    bank, key, store_path, forbidden = get_config_for_mode("demo")
    assert bank == "ci-agent-demo"
    assert store_path == os.path.join("data", "demo_experiences.json")
    assert "ci-agent-development" in forbidden
    assert "ci-agent-demo" not in forbidden

def test_demo_mode_cannot_target_development_bank():
    """Verify HindsightService prevents targeting ci-agent-development when in demo mode."""
    bank, key, store_path, forbidden = get_config_for_mode("demo")
    with pytest.raises(ValueError, match="Safety Violation: Cannot interact with protected bank"):
        HindsightService(
            bank_id="ci-agent-development",
            api_key=key,
            forbidden_banks=forbidden
        )

def test_development_mode_cannot_target_demo_bank():
    """Verify HindsightService prevents targeting ci-agent-demo when in development mode."""
    bank, key, store_path, forbidden = get_config_for_mode("development")
    with pytest.raises(ValueError, match="Safety Violation: Cannot interact with protected bank"):
        HindsightService(
            bank_id="ci-agent-demo",
            api_key=key,
            forbidden_banks=forbidden
        )

def test_local_experience_stores_remain_separated(tmp_path):
    """Verify that development and demo stores operate on separate files without cross-contamination."""
    dev_file = str(tmp_path / "experiences.json")
    demo_file = str(tmp_path / "demo_experiences.json")

    dev_store = ExperienceStore(storage_path=dev_file)
    demo_store = ExperienceStore(storage_path=demo_file)

    # Add experience to dev store
    dev_exp = Experience(
        experience_id="dev-001",
        timestamp="2026-09-29T00:00:00Z",
        repository="acme/dev-repo",
        workflow="build",
        failure_signature="npm_install_timeout",
        error_type="FetchError",
        error_message="timeout",
        environment="node:20",
        action_taken="retry",
        action_result="failure",
        resolution="failed",
        lesson_learned="dev lesson"
    )
    dev_store.add(dev_exp)

    # Demo store must still be empty
    assert len(demo_store.list_all()) == 0
    assert len(dev_store.list_all()) == 1

    # Add experience to demo store
    demo_exp = Experience(
        experience_id="demo-001",
        timestamp="2026-09-29T00:00:00Z",
        repository="acme/demo-repo",
        workflow="build",
        failure_signature="npm_install_timeout",
        error_type="FetchError",
        error_message="timeout",
        environment="node:20",
        action_taken="switched mirror",
        action_result="success",
        resolution="succeeded",
        lesson_learned="demo lesson"
    )
    demo_store.add(demo_exp)

    # Verify completely separated contents
    assert len(dev_store.list_all()) == 1
    assert dev_store.get("dev-001") is not None
    assert dev_store.get("demo-001") is None

    assert len(demo_store.list_all()) == 1
    assert demo_store.get("demo-001") is not None
    assert demo_store.get("dev-001") is None
