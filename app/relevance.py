import re
from typing import List, Dict, Any, Optional
from app.models import FailureInfo, RecalledExperienceItem

class RelevanceFilter:
    """
    Evaluates recalled Hindsight memory units against the current CI failure context.
    Filters out semantically similar but operationally irrelevant memories (e.g. Python vs npm).
    """

    RELEVANCE_THRESHOLD = 0.55

    @classmethod
    def score_memory(cls, memory_text: str, current_failure: FailureInfo, metadata: Optional[Dict[str, Any]] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        metadata = metadata or {}
        tags = tags or []
        text_lower = memory_text.lower()
        score = 0.0
        reasons = []

        # 1. Failure Signature Match
        curr_sig = current_failure.failure_signature.lower()
        if curr_sig in text_lower or (tags and curr_sig in [t.lower() for t in tags]) or (metadata.get("failure_signature", "").lower() == curr_sig):
            score += 0.45
            reasons.append(f"Direct match on failure signature '{current_failure.failure_signature}'")
        else:
            # Partial signature match (e.g., "timeout" or "install")
            sig_tokens = [t for t in curr_sig.split("_") if len(t) > 2]
            token_matches = [t for t in sig_tokens if t in text_lower]
            if len(token_matches) >= 2:
                score += 0.25
                reasons.append(f"Partial match on signature keywords: {', '.join(token_matches)}")

        # 2. Ecosystem Compatibility vs Conflict Check
        is_npm_target = "npm" in curr_sig or "node" in curr_sig or "javascript" in curr_sig
        is_python_target = "python" in curr_sig or "pip" in curr_sig

        python_keywords = ["python", "pip", "pypi", "requirements.txt", "setup.py", "wheel", "virtualenv"]
        npm_keywords = ["npm", "node", "registry.npmjs", "package.json", "node_modules", "package-lock", "yarn", "pnpm"]

        if is_npm_target:
            has_python_clues = any(k in text_lower for k in python_keywords)
            has_npm_clues = any(k in text_lower for k in npm_keywords)
            if has_python_clues and not has_npm_clues:
                score -= 0.50
                reasons.append("Conflicting ecosystem: relates to Python rather than npm/Node.js")
            elif has_npm_clues:
                score += 0.20
                reasons.append("Matching npm/Node.js ecosystem")
        elif is_python_target:
            has_npm_clues = any(k in text_lower for k in npm_keywords)
            has_python_clues = any(k in text_lower for k in python_keywords)
            if has_npm_clues and not has_python_clues:
                score -= 0.50
                reasons.append("Conflicting ecosystem: relates to npm rather than Python")
            elif has_python_clues:
                score += 0.20
                reasons.append("Matching Python ecosystem")

        # 3. Error Type / Keywords Match
        curr_error_type = current_failure.error_type.lower()
        if curr_error_type and curr_error_type in text_lower:
            score += 0.15
            reasons.append(f"Matches error type '{current_failure.error_type}'")

        if "timeout" in current_failure.failure_signature and "timeout" in text_lower:
            score += 0.10
        if "registry" in text_lower and "registry" in current_failure.error_message.lower():
            score += 0.10

        # 4. Repository / Workflow Match
        if current_failure.repository.lower() in text_lower:
            score += 0.05
            reasons.append("Matches target repository")

        # 5. Extract Outcome & Action Clues
        extracted_result = None
        extracted_action = None
        extracted_lesson = None

        if "result: failure" in text_lower or "action result: failure" in text_lower or "failed" in text_lower and "resolved the issue" not in text_lower:
            if "did not solve" in text_lower or "failed" in text_lower:
                extracted_result = "failure"
        if "result: success" in text_lower or "action result: success" in text_lower or "completed successfully" in text_lower or "fix succeeded" in text_lower or "resolved the issue" in text_lower:
            extracted_result = "success"

        # Check metadata override
        if metadata.get("action_result"):
            extracted_result = metadata["action_result"].lower()

        # Action clues
        if "retry npm install" in text_lower or "retrying" in text_lower:
            extracted_action = "Retry npm install"
        elif "registry configuration" in text_lower or "switched to the correct accessible registry" in text_lower:
            extracted_action = "Verify and switch npm registry configuration"

        # Lesson clues
        if "lesson:" in text_lower or "lesson learned:" in text_lower:
            m = re.search(r"lesson(?: learned)?:\s*([^\n\.]+)", memory_text, re.IGNORECASE)
            if m:
                extracted_lesson = m.group(1).strip()

        # Clamp score between 0.0 and 1.0
        score = max(0.0, min(1.0, round(score, 2)))

        # Determine status
        if score >= cls.RELEVANCE_THRESHOLD:
            status = "Used for recommendation" if (extracted_result or "lesson" in text_lower or "timeout" in text_lower) else "Relevant"
            reason = " | ".join(reasons) if reasons else "Contextually relevant to current CI failure"
        else:
            status = "Low relevance"
            reason = " | ".join(reasons) if reasons else "Insufficient operational overlap with current failure context"

        # Extract experience ID if present
        exp_id_match = re.search(r"\[(exp-[a-zA-Z0-9\-]+)\]", memory_text)
        exp_id = exp_id_match.group(1) if exp_id_match else metadata.get("experience_id")

        return {
            "score": score,
            "status": status,
            "reason": reason,
            "extracted_action": extracted_action,
            "extracted_result": extracted_result,
            "extracted_lesson": extracted_lesson,
            "experience_id": exp_id
        }

    @classmethod
    def filter_and_rank(cls, raw_memories: List[Any], current_failure: FailureInfo) -> List[RecalledExperienceItem]:
        processed: List[RecalledExperienceItem] = []

        for item in raw_memories:
            text = getattr(item, "text", str(item))
            mem_type = getattr(item, "type", "observation")
            item_id = getattr(item, "id", None)
            metadata = getattr(item, "metadata", {}) or {}
            tags = getattr(item, "tags", []) or []

            eval_res = cls.score_memory(
                memory_text=text,
                current_failure=current_failure,
                metadata=metadata,
                tags=tags
            )

            processed.append(
                RecalledExperienceItem(
                    id=item_id,
                    experience_id=eval_res["experience_id"],
                    text=text,
                    memory_type=mem_type,
                    relevance_score=eval_res["score"],
                    relevance_status=eval_res["status"],
                    relevance_reason=eval_res["reason"],
                    extracted_action=eval_res["extracted_action"],
                    extracted_result=eval_res["extracted_result"],
                    extracted_lesson=eval_res["extracted_lesson"]
                )
            )

        # Sort descending by relevance score
        processed.sort(key=lambda x: x.relevance_score, reverse=True)
        return processed
