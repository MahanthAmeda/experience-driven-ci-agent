import pytest
from unittest.mock import MagicMock
from app.models import FailureInfo
from app.relevance import RelevanceFilter

def test_relevance_filters_unrelated_python_experience():
    """C. Relevance filtering: unrelated Python experience does not influence npm recommendation."""
    current_failure = FailureInfo(
        repository="acme/ecommerce-web",
        workflow="ci-build",
        failure_signature="npm_install_timeout",
        error_type="RegistryTimeoutError",
        error_message="ETIMEDOUT: fetch failed for https://registry.npmjs.org/@acme/core",
        environment="node:18 / ubuntu-latest"
    )

    # 1. Unrelated Python memory (such as Milestone 1 verification memory)
    python_mem = MagicMock()
    python_mem.id = "mem-python-001"
    python_mem.text = (
        "Development verification test: A Python package installation failed because of a dependency conflict. "
        "The engineer resolved the issue by pinning compatible package versions. The fix succeeded. "
        "Lesson: check dependency compatibility before retrying installation."
    )
    python_mem.type = "observation"
    python_mem.metadata = {"failure_signature": "python_package_install_failure", "action_result": "success"}
    python_mem.tags = ["python_package_install_failure", "result:success"]

    # 2. Relevant npm install timeout memory
    npm_mem = MagicMock()
    npm_mem.id = "mem-npm-001"
    npm_mem.text = (
        "CI Failure Incident [exp-npm-001]: npm_install_timeout. Error: ETIMEDOUT fetching registry.npmjs.org. "
        "Action Taken: Retry npm install. Action Result: FAILURE (FAILED). "
        "Resolution Details: Retry did not solve the issue. "
        "Lesson Learned: Repeated retries are ineffective when registry/network path itself is unavailable."
    )
    npm_mem.type = "experience"
    npm_mem.metadata = {"failure_signature": "npm_install_timeout", "action_result": "failure"}
    npm_mem.tags = ["npm_install_timeout", "result:failure"]

    results = RelevanceFilter.filter_and_rank([python_mem, npm_mem], current_failure)

    assert len(results) == 2

    # Find the python and npm results
    py_res = next(r for r in results if r.id == "mem-python-001")
    npm_res = next(r for r in results if r.id == "mem-npm-001")

    # Python memory must be marked as "Low relevance"
    assert py_res.relevance_status == "Low relevance"
    assert "Python" in py_res.relevance_reason
    assert py_res.relevance_score < 0.50

    # npm memory must be marked as "Used for recommendation" or "Relevant"
    assert npm_res.relevance_status in ("Used for recommendation", "Relevant")
    assert npm_res.relevance_score >= 0.55
    assert npm_res.extracted_result == "failure"
