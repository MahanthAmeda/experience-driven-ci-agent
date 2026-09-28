import os
from typing import List, Dict, Any, Optional
from hindsight_client import Hindsight
from app.config import HINDSIGHT_API_URL, ACTIVE_API_KEY, ACTIVE_BANK_ID, FORBIDDEN_BANKS
from app.models import Experience

class HindsightService:
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        bank_id: Optional[str] = None,
        forbidden_banks: Optional[set] = None
    ):
        self.api_url = api_url or HINDSIGHT_API_URL
        self.api_key = api_key or ACTIVE_API_KEY
        self.bank_id = bank_id or ACTIVE_BANK_ID
        self.forbidden_banks = forbidden_banks if forbidden_banks is not None else FORBIDDEN_BANKS

        # Guard: NEVER allow interacting with forbidden bank in current mode
        if self.bank_id in self.forbidden_banks:
            raise ValueError(f"Safety Violation: Cannot interact with protected bank '{self.bank_id}' in current mode!")

        if not self.api_key:
            raise ValueError(f"API key is required to initialize HindsightService for bank '{self.bank_id}'.")

        self._client = None

    @property
    def client(self) -> Hindsight:
        if self._client is not None:
            return self._client
        return Hindsight(base_url=self.api_url, api_key=self.api_key)

    @client.setter
    def client(self, value):
        self._client = value

    def health_check(self) -> Dict[str, Any]:
        """Verify connectivity and bank accessibility."""
        config = self.client.get_bank_config(bank_id=self.bank_id)
        return {
            "status": "connected",
            "bank_id": self.bank_id,
            "api_url": self.api_url,
            "bank_config_retrieved": bool(config)
        }

    def format_experience_content(self, exp: Experience) -> str:
        """
        Format experience into a rich natural language narrative
        optimized for Hindsight's TEMPR memory extraction and semantic retrieval.
        """
        outcome_label = "SUCCESSFUL" if exp.action_result.lower() == "success" else "FAILED"
        narrative = (
            f"CI Failure Incident [{exp.experience_id}] on {exp.timestamp}.\n"
            f"Repository: {exp.repository} | Workflow: {exp.workflow} | Environment: {exp.environment}.\n"
            f"Failure Signature: {exp.failure_signature} | Error Type: {exp.error_type}.\n"
            f"Error Details: {exp.error_message}.\n"
            f"Suspected Cause: {exp.suspected_cause or 'Under investigation'}.\n"
            f"Action Taken by Engineer: {exp.action_taken}.\n"
            f"Action Result: {exp.action_result.upper()} ({outcome_label}).\n"
            f"Resolution Details: {exp.resolution}.\n"
            f"Lesson Learned: {exp.lesson_learned}"
        )
        return narrative

    def retain_experience(self, exp: Experience) -> Dict[str, Any]:
        """
        Retain an experience into Hindsight memory bank.
        Synchronous by default.
        """
        content = self.format_experience_content(exp)
        tags = [
            exp.failure_signature,
            exp.error_type,
            f"result:{exp.action_result.lower()}",
            exp.experience_id
        ]
        metadata = {
            "experience_id": exp.experience_id,
            "failure_signature": exp.failure_signature,
            "action_result": exp.action_result.lower(),
            "repository": exp.repository
        }

        resp = self.client.retain(
            bank_id=self.bank_id,
            content=content,
            tags=tags,
            metadata=metadata
        )

        is_async = getattr(resp, "var_async", False)
        op_id = getattr(resp, "operation_id", None)
        success = getattr(resp, "success", False)
        items_count = getattr(resp, "items_count", 0)

        # If async processing is ever returned, use official get_operation_status
        if is_async and op_id:
            op_status = self.client.operations.get_operation_status(
                bank_id=self.bank_id,
                operation_id=op_id
            )
            status_str = getattr(op_status, "status", "unknown")
        else:
            status_str = "completed"

        return {
            "success": success,
            "bank_id": self.bank_id,
            "experience_id": exp.experience_id,
            "async": is_async,
            "operation_id": op_id,
            "status": status_str,
            "items_count": items_count
        }

    def recall_memories(self, query: str, budget: str = "mid") -> List[Any]:
        """
        Execute recall query against Hindsight TEMPR retrieval engine.
        """
        resp = self.client.recall(
            bank_id=self.bank_id,
            query=query,
            budget=budget,
            max_tokens=4096
        )
        return getattr(resp, "results", [])

    def close(self):
        if hasattr(self, "client") and self.client:
            self.client.close()
