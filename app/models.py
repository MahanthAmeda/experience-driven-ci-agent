from enum import Enum
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field

class FailureSignature(str, Enum):
    npm_install_timeout = "npm_install_timeout"
    npm_dependency_conflict = "npm_dependency_conflict"
    python_package_install_failure = "python_package_install_failure"
    test_failure = "test_failure"
    compilation_failure = "compilation_failure"
    docker_build_failure = "docker_build_failure"
    missing_environment_variable = "missing_environment_variable"
    authentication_failure = "authentication_failure"
    lint_failure = "lint_failure"
    deployment_failure = "deployment_failure"

class ActionResult(str, Enum):
    success = "success"
    failure = "failure"

class FailureInfo(BaseModel):
    repository: str = Field(..., description="Repository name or slug, e.g. acme/web-app")
    workflow: str = Field(..., description="CI workflow name, e.g. ci-build-test")
    failure_signature: str = Field(..., description="Classification signature of the failure")
    error_type: str = Field(..., description="Category or exception type of error")
    error_message: str = Field(..., description="Raw or extracted error output")
    environment: str = Field(default="ubuntu-latest", description="Runtime environment or runner image")
    suspected_cause: Optional[str] = Field(None, description="Initial suspected cause")

class Experience(BaseModel):
    experience_id: str = Field(..., description="Unique experience identifier")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    repository: str
    workflow: str
    failure_signature: str
    error_type: str
    error_message: str
    environment: str
    suspected_cause: Optional[str] = None
    action_taken: str
    action_result: str = Field(..., description="'success' or 'failure'")
    resolution: str
    lesson_learned: str

class RecalledExperienceItem(BaseModel):
    id: Optional[str] = None
    experience_id: Optional[str] = None
    text: str
    memory_type: str = "observation"
    relevance_score: float = 0.0
    relevance_status: str = "Low relevance"  # "Relevant", "Low relevance", "Used for recommendation"
    relevance_reason: str = ""
    extracted_action: Optional[str] = None
    extracted_result: Optional[str] = None   # "success" or "failure"
    extracted_resolution: Optional[str] = None
    extracted_lesson: Optional[str] = None

class AnalyseRequest(BaseModel):
    failure: FailureInfo
    memory_enabled: bool = True

class AnalyseResponse(BaseModel):
    current_failure: FailureInfo
    memory_enabled: bool
    recalled_experiences: List[RecalledExperienceItem] = []
    relevant_experiences: List[RecalledExperienceItem] = []
    low_relevance_experiences: List[RecalledExperienceItem] = []
    recommendation: str
    reasoning: str
    influencing_experiences: List[str] = []

class OutcomeUpdateRequest(BaseModel):
    action_taken: str
    action_result: str
    resolution: str
    lesson_learned: str
