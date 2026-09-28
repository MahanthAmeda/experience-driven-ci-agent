import pytest
from app.models import FailureInfo, RecalledExperienceItem
from app.learning_engine import LearningEngine

@pytest.fixture
def current_npm_failure():
    return FailureInfo(
        repository="acme/web-frontend",
        workflow="ci-pipeline",
        failure_signature="npm_install_timeout",
        error_type="RegistryTimeoutError",
        error_message="ETIMEDOUT: timeout while fetching https://registry.npmjs.org/@acme/ui",
        environment="node:18 / ubuntu-latest"
    )

def test_learning_progression_stage_1_no_prior_memory(current_npm_failure):
    """Stage 1: When no prior experiences exist, initial baseline recommendation is produced."""
    response = LearningEngine.synthesize(
        current_failure=current_npm_failure,
        recalled_items=[],
        memory_enabled=True
    )
    assert "Initial recommendation" in response.recommendation
    assert "Retry" in response.recommendation
    assert len(response.relevant_experiences) == 0

def test_learning_progression_stage_2_after_failed_retry(current_npm_failure):
    """Stage 2: After Experience 1 (failed retry), recommendation changes away from naive retry."""
    exp1_item = RecalledExperienceItem(
        id="mem-1",
        experience_id="exp-npm-001",
        text="CI Failure [exp-npm-001]: Action Taken: Retry npm install. Action Result: FAILURE. Resolution: Retry did not solve the issue. Lesson: Repeated retries are ineffective.",
        memory_type="experience",
        relevance_score=0.90,
        relevance_status="Used for recommendation",
        relevance_reason="Direct match on npm_install_timeout",
        extracted_action="Retry npm install",
        extracted_result="failure",
        extracted_lesson="Repeated retries are ineffective when the npm registry/network path itself is unavailable."
    )

    response = LearningEngine.synthesize(
        current_failure=current_npm_failure,
        recalled_items=[exp1_item],
        memory_enabled=True
    )

    # Must NOT blindly recommend retry
    assert "Do NOT repeatedly retry npm install" in response.recommendation
    assert "investigate" in response.recommendation.lower() or "configuration" in response.recommendation.lower()
    assert "exp-npm-001" in response.influencing_experiences
    assert "failed" in response.reasoning.lower()

def test_learning_progression_stage_3_after_successful_registry_fix(current_npm_failure):
    """Stage 3: After Experience 2 (successful registry fix), recommendation prioritizes proven fix."""
    exp1_item = RecalledExperienceItem(
        id="mem-1",
        experience_id="exp-npm-001",
        text="CI Failure [exp-npm-001]: Action Taken: Retry npm install. Action Result: FAILURE. Resolution: Retry did not solve the issue. Lesson: Repeated retries are ineffective.",
        memory_type="experience",
        relevance_score=0.90,
        relevance_status="Used for recommendation",
        relevance_reason="Direct match on npm_install_timeout",
        extracted_action="Retry npm install",
        extracted_result="failure"
    )

    exp2_item = RecalledExperienceItem(
        id="mem-2",
        experience_id="exp-npm-002",
        text="CI Failure [exp-npm-002]: Action Taken: Verified npm registry configuration. Action Result: SUCCESS. Resolution: Completed successfully. Lesson: Verify registry configuration before retrying.",
        memory_type="experience",
        relevance_score=0.92,
        relevance_status="Used for recommendation",
        relevance_reason="Direct match on npm_install_timeout",
        extracted_action="Verify and switch npm registry configuration",
        extracted_result="success"
    )

    response = LearningEngine.synthesize(
        current_failure=current_npm_failure,
        recalled_items=[exp1_item, exp2_item],
        memory_enabled=True
    )

    # Must compare BOTH outcomes and prioritize the successful action
    assert "Previous similar failures show that retrying did not resolve the problem" in response.recommendation
    assert "succeeded" in response.recommendation
    assert "Verify the registry" in response.recommendation
    assert "exp-npm-001" in response.influencing_experiences
    assert "exp-npm-002" in response.influencing_experiences
    assert "Comparative outcome" in response.reasoning or "Empirical outcome" in response.reasoning
