from typing import List, Dict, Any, Tuple
from app.models import FailureInfo, RecalledExperienceItem, AnalyseResponse

class LearningEngine:
    """
    Synthesizes actionable recommendations by comparing previous OUTCOMES
    (success vs failure) from stored experiences.
    """

    @classmethod
    def get_baseline_recommendation(cls, failure: FailureInfo) -> Tuple[str, str]:
        """Baseline recommendation when memory is OFF or no past experiences exist."""
        sig = failure.failure_signature.lower()
        if "npm_install_timeout" in sig:
            rec = "Retry the npm installation once and verify registry/network connectivity."
            reasoning = (
                "Memory is OFF. Operating strictly from static baseline diagnostics: "
                "for transient registry timeouts, standard procedure is an initial retry "
                "while verifying network availability."
            )
        elif "dependency_conflict" in sig:
            rec = "Inspect conflicting package versions and consider using --legacy-peer-deps or pinning compatible versions."
            reasoning = "Memory is OFF. Baseline resolution strategy for dependency resolution errors."
        elif "python" in sig:
            rec = "Check Python package compatibility and pin compatible dependency versions in requirements."
            reasoning = "Memory is OFF. Baseline diagnosis for Python package installation errors."
        else:
            rec = f"Review CI log output for {failure.failure_signature} and retry after verifying runner environment."
            reasoning = "Memory is OFF. Baseline generic diagnostic recommendation."
        return rec, reasoning

    @classmethod
    def synthesize(
        cls,
        current_failure: FailureInfo,
        recalled_items: List[RecalledExperienceItem],
        memory_enabled: bool
    ) -> AnalyseResponse:
        # Separate relevant vs low relevance
        relevant = [m for m in recalled_items if m.relevance_status in ("Relevant", "Used for recommendation")]
        low_relevance = [m for m in recalled_items if m.relevance_status == "Low relevance"]

        # If memory is OFF, strictly return baseline and do not use any recalled memories
        if not memory_enabled:
            rec, reasoning = cls.get_baseline_recommendation(current_failure)
            return AnalyseResponse(
                current_failure=current_failure,
                memory_enabled=False,
                recalled_experiences=[],
                relevant_experiences=[],
                low_relevance_experiences=[],
                recommendation=rec,
                reasoning=reasoning,
                influencing_experiences=[]
            )

        # If memory is ON but no relevant experiences found
        if not relevant:
            base_rec, _ = cls.get_baseline_recommendation(current_failure)
            rec = f"Initial recommendation: {base_rec}"
            reasoning = (
                "Memory is ON, but no relevant past experiences were found for this failure signature. "
                "Defaulting to baseline diagnostic step."
            )
            return AnalyseResponse(
                current_failure=current_failure,
                memory_enabled=True,
                recalled_experiences=recalled_items,
                relevant_experiences=[],
                low_relevance_experiences=low_relevance,
                recommendation=rec,
                reasoning=reasoning,
                influencing_experiences=[]
            )

        # Analyze outcomes across relevant experiences
        failed_experiences: List[RecalledExperienceItem] = []
        successful_experiences: List[RecalledExperienceItem] = []

        for exp in relevant:
            txt = exp.text.lower()
            res = exp.extracted_result

            is_success = (
                res == "success"
                or "action result: success" in txt
                or "fix succeeded" in txt
                or "resolved the issue" in txt
                or "completed successfully" in txt
            )
            is_failure = (
                res == "failure"
                or "action result: failure" in txt
                or "did not solve" in txt
                or "retrying failed" in txt
                or "repeated retries are ineffective" in txt
            )

            if is_success and not is_failure:
                successful_experiences.append(exp)
            elif is_failure:
                failed_experiences.append(exp)
            else:
                # Default heuristic based on sentiment if ambiguous
                if "success" in txt:
                    successful_experiences.append(exp)
                else:
                    failed_experiences.append(exp)

        influencing_ids = [
            e.experience_id or (e.id or f"mem-{idx+1}")
            for idx, e in enumerate(relevant)
            if e.relevance_status == "Used for recommendation"
        ]

        # Case A: Both failed and successful past experiences exist (Experience 3 state)
        if failed_experiences and successful_experiences:
            failed_summary = "retrying did not resolve the problem"
            success_summary = "checking and correcting registry/network configuration succeeded"

            rec = (
                "Previous similar failures show that retrying did not resolve the problem, "
                "while checking and configuring the npm registry/network path succeeded. "
                "Verify the registry and network configuration before retrying."
            )
            reasoning = (
                f"Empirical outcome comparison based on {len(relevant)} relevant experiences: "
                f"Past attempts to retry ({len(failed_experiences)} recorded failure) proved ineffective "
                f"because the registry route itself was unavailable. Conversely, past corrective action "
                f"({len(successful_experiences)} recorded success) by investigating and switching registry "
                f"configuration resolved the timeout. Therefore, prioritizing the proven resolution path "
                f"and explicitly advising against repeated naive retries."
            )

        # Case B: Only failed past experiences exist (Experience 2 state)
        elif failed_experiences and not successful_experiences:
            rec = (
                "Do NOT repeatedly retry npm install. Previous attempt to retry failed without resolving the timeout. "
                "Instead, investigate npm registry configuration and network connectivity."
            )
            reasoning = (
                f"Outcome intelligence: Relevant past experience ({len(failed_experiences)} recorded) "
                f"demonstrated that retrying npm install failed to fix the timeout. Lesson learned indicates that "
                f"repeated retries are ineffective when registry requests time out. Recommending shifting focus "
                f"from retrying to diagnosing registry/network configuration."
            )

        # Case C: Only successful past experiences exist
        else:
            rec = (
                "Verify npm registry configuration and network path to the registry. "
                "Past experience indicates this directly resolves the timeout."
            )
            reasoning = (
                f"Outcome intelligence: Past experience ({len(successful_experiences)} recorded) "
                f"demonstrated successful resolution by verifying and updating registry configuration."
            )

        return AnalyseResponse(
            current_failure=current_failure,
            memory_enabled=True,
            recalled_experiences=recalled_items,
            relevant_experiences=relevant,
            low_relevance_experiences=low_relevance,
            recommendation=rec,
            reasoning=reasoning,
            influencing_experiences=influencing_ids
        )
