"""
Progression Demonstration Script for Milestone 2:
Executes the Experience 1 -> Experience 2 -> Experience 3 live progression
against the real Hindsight development bank (ci-agent-development).
Demonstrates:
1. Memory OFF vs Memory ON
2. Relevance filtering (ignoring Python verification memory)
3. Experience 1 (Failed retry retained)
4. Experience 2 (Recalls Exp 1, adapts recommendation, successful registry fix retained)
5. Experience 3 (Recalls Exp 1 & 2, compares outcomes, prioritizes proven fix)
"""

import sys
import json
from datetime import datetime, timezone
from app.config import ACTIVE_BANK_ID, HINDSIGHT_API_URL
from app.models import FailureInfo, Experience, AnalyseRequest
from app.hindsight_service import HindsightService
from app.experience_store import ExperienceStore
from app.relevance import RelevanceFilter
from app.learning_engine import LearningEngine

def print_separator(title: str):
    print("\n" + "=" * 70)
    print(f" {title.upper()}")
    print("=" * 70)

def main():
    print_separator("Milestone 2: Real Hindsight Experience Progression Test")
    print(f"Target Bank: {ACTIVE_BANK_ID}")
    print(f"API URL: {HINDSIGHT_API_URL}")
    print("API Key: [REDACTED - PRESENT]")

    # Initialize services
    hindsight = HindsightService()
    store = ExperienceStore(storage_path="data/demo_experiences.json")

    # Step 0: Health check
    health = hindsight.health_check()
    print(f"Health Check: {health['status']} (Bank config verified: {health['bank_config_retrieved']})")

    # Current CI Failure template for npm_install_timeout
    failure_1 = FailureInfo(
        repository="acme/web-portal",
        workflow="ci-build-and-test",
        failure_signature="npm_install_timeout",
        error_type="FetchError",
        error_message="npm ERR! code ETIMEDOUT fetch failed https://registry.npmjs.org/@acme/core",
        environment="node:18-alpine / ubuntu-latest",
        suspected_cause="Registry timeout or unreachable network route"
    )

    # -------------------------------------------------------------
    # DEMONSTRATION: MEMORY OFF vs MEMORY ON (Before Learning)
    # -------------------------------------------------------------
    print_separator("Comparison: Memory OFF vs Memory ON")

    # Memory OFF
    res_mem_off = LearningEngine.synthesize(
        current_failure=failure_1,
        recalled_items=[],
        memory_enabled=False
    )
    print("[Mode: MEMORY OFF]")
    print(f"Recommendation: {res_mem_off.recommendation}")
    print(f"Reasoning:      {res_mem_off.reasoning}")
    print(f"Recalled Items: {len(res_mem_off.recalled_experiences)}")

    # Memory ON (Querying Hindsight now)
    raw_memories_initial = hindsight.recall_memories(
        query="npm install failure timeout ETIMEDOUT registry.npmjs.org"
    )
    scored_initial = RelevanceFilter.filter_and_rank(raw_memories_initial, failure_1)
    res_mem_on_initial = LearningEngine.synthesize(
        current_failure=failure_1,
        recalled_items=scored_initial,
        memory_enabled=True
    )
    print("\n[Mode: MEMORY ON (Initial State)]")
    print(f"Recommendation: {res_mem_on_initial.recommendation}")
    print(f"Reasoning:      {res_mem_on_initial.reasoning}")
    print(f"Total Recalled: {len(res_mem_on_initial.recalled_experiences)}")
    print(f"Relevant:       {len(res_mem_on_initial.relevant_experiences)}")
    print(f"Low Relevance:  {len(res_mem_on_initial.low_relevance_experiences)}")

    # Check if existing Python memory is present and filtered
    python_memories = [m for m in scored_initial if "python" in m.text.lower()]
    if python_memories:
        print("\n[Relevance Filter in Action on Pre-existing Memory]")
        for pm in python_memories[:2]:
            print(f"- Text snippet:    {pm.text[:90]}...")
            print(f"  Relevance Score: {pm.relevance_score}")
            print(f"  Status:          {pm.relevance_status}")
            print(f"  Reason:          {pm.relevance_reason}")

    # -------------------------------------------------------------
    # EXPERIENCE 1: Initial Failure -> Retry Action -> FAILED
    # -------------------------------------------------------------
    print_separator("Experience 1: Recording Failed Retry Action")
    exp1 = Experience(
        experience_id="exp-npm-001",
        timestamp=datetime.now(timezone.utc).isoformat(),
        repository="acme/web-portal",
        workflow="ci-build-and-test",
        failure_signature="npm_install_timeout",
        error_type="FetchError",
        error_message="npm ERR! code ETIMEDOUT fetch failed https://registry.npmjs.org/@acme/core",
        environment="node:18-alpine / ubuntu-latest",
        suspected_cause="Transient registry timeout",
        action_taken="Retry npm install",
        action_result="failure",
        resolution="Retry did not solve the issue. Package registry request timed out repeatedly.",
        lesson_learned="Repeated retries are ineffective when the npm registry/network path itself is unavailable."
    )

    store.add(exp1)
    retain_res1 = hindsight.retain_experience(exp1)
    print(f"Retained Experience 1 in Hindsight: success={retain_res1['success']}, items={retain_res1['items_count']}")
    print(f"Action Taken:  {exp1.action_taken}")
    print(f"Action Result: {exp1.action_result.upper()} (failure)")
    print(f"Lesson:        {exp1.lesson_learned}")

    # -------------------------------------------------------------
    # EXPERIENCE 2: Second Failure -> Recalls Exp 1 -> Adapts Rec
    # -------------------------------------------------------------
    print_separator("Experience 2: Recalls Exp 1 -> Recommendation Adapts")

    failure_2 = FailureInfo(
        repository="acme/payment-service",
        workflow="ci-pipeline",
        failure_signature="npm_install_timeout",
        error_type="FetchError",
        error_message="npm ERR! code ETIMEDOUT fetch failed https://registry.npmjs.org/@acme/payment-sdk",
        environment="node:18-alpine / ubuntu-latest",
        suspected_cause="npm registry timeout"
    )

    # Recall from Hindsight
    raw_memories_exp2 = hindsight.recall_memories(
        query="CI failure npm install timeout ETIMEDOUT registry"
    )
    scored_exp2 = RelevanceFilter.filter_and_rank(raw_memories_exp2, failure_2)
    analysis_exp2 = LearningEngine.synthesize(
        current_failure=failure_2,
        recalled_items=scored_exp2,
        memory_enabled=True
    )

    print(f"Total Memories Recalled:   {len(analysis_exp2.recalled_experiences)}")
    print(f"Relevant Memories Used:    {len(analysis_exp2.relevant_experiences)}")
    print(f"Low Relevance Memories:    {len(analysis_exp2.low_relevance_experiences)}")
    print(f"Influencing Experiences:   {analysis_exp2.influencing_experiences}")
    print(f"\nNEW RECOMMENDATION AFTER EXP 1:")
    print(f"> {analysis_exp2.recommendation}")
    print(f"\nREASONING (EXPLAINING WHY PREVIOUS OUTCOME INFLUENCED IT):")
    print(f"> {analysis_exp2.reasoning}")

    # Simulate engineer following new recommendation: verifying registry configuration
    print("\nSimulating Engineer Action based on recommendation...")
    exp2 = Experience(
        experience_id="exp-npm-002",
        timestamp=datetime.now(timezone.utc).isoformat(),
        repository="acme/payment-service",
        workflow="ci-pipeline",
        failure_signature="npm_install_timeout",
        error_type="FetchError",
        error_message="npm ERR! code ETIMEDOUT fetch failed https://registry.npmjs.org/@acme/payment-sdk",
        environment="node:18-alpine / ubuntu-latest",
        suspected_cause="Misconfigured internal npm registry mirror route",
        action_taken="Verified npm registry configuration and switched to the correct accessible registry/network configuration.",
        action_result="success",
        resolution="npm installation completed successfully after configuring the accessible registry URL.",
        lesson_learned="When npm registry requests repeatedly timeout, verify registry/network configuration before repeatedly retrying."
    )

    store.add(exp2)
    retain_res2 = hindsight.retain_experience(exp2)
    print(f"Retained Experience 2 in Hindsight: success={retain_res2['success']}, items={retain_res2['items_count']}")
    print(f"Action Taken:  {exp2.action_taken}")
    print(f"Action Result: {exp2.action_result.upper()} (success)")
    print(f"Lesson:        {exp2.lesson_learned}")

    # -------------------------------------------------------------
    # EXPERIENCE 3: Third Failure -> Recalls Exp 1 & 2 -> Prioritizes Fix
    # -------------------------------------------------------------
    print_separator("Experience 3: Recalls Exp 1 & 2 -> Prioritizes Proven Fix")

    failure_3 = FailureInfo(
        repository="acme/notification-service",
        workflow="ci-build",
        failure_signature="npm_install_timeout",
        error_type="FetchError",
        error_message="npm ERR! code ETIMEDOUT fetch failed https://registry.npmjs.org/@acme/common-lib",
        environment="node:18-alpine / ubuntu-latest",
        suspected_cause="Package registry request timeout"
    )

    # Recall from Hindsight (now contains both Exp 1 and Exp 2)
    raw_memories_exp3 = hindsight.recall_memories(
        query="CI failure npm install timeout ETIMEDOUT registry action outcome"
    )
    scored_exp3 = RelevanceFilter.filter_and_rank(raw_memories_exp3, failure_3)
    analysis_exp3 = LearningEngine.synthesize(
        current_failure=failure_3,
        recalled_items=scored_exp3,
        memory_enabled=True
    )

    print(f"Total Memories Recalled:   {len(analysis_exp3.recalled_experiences)}")
    print(f"Relevant Memories Used:    {len(analysis_exp3.relevant_experiences)}")
    print(f"Low Relevance Memories:    {len(analysis_exp3.low_relevance_experiences)}")
    print(f"Influencing Experiences:   {analysis_exp3.influencing_experiences}")
    print(f"\nNEW RECOMMENDATION AFTER EXP 1 & EXP 2:")
    print(f"> {analysis_exp3.recommendation}")
    print(f"\nREASONING (COMPARING OUTCOMES):")
    print(f"> {analysis_exp3.reasoning}")

    # Record and retain Experience 3
    exp3 = Experience(
        experience_id="exp-npm-003",
        timestamp=datetime.now(timezone.utc).isoformat(),
        repository="acme/notification-service",
        workflow="ci-build",
        failure_signature="npm_install_timeout",
        error_type="FetchError",
        error_message="npm ERR! code ETIMEDOUT fetch failed https://registry.npmjs.org/@acme/common-lib",
        environment="node:18-alpine / ubuntu-latest",
        suspected_cause="Outdated npm registry setting in CI job",
        action_taken="Checked registry configuration upfront and pointed to internal mirror without retrying.",
        action_result="success",
        resolution="Build succeeded immediately without timeout delays.",
        lesson_learned="Proactively checking registry configuration saves CI build time by avoiding failed retries."
    )

    store.add(exp3)
    retain_res3 = hindsight.retain_experience(exp3)
    print(f"\nRetained Experience 3 in Hindsight: success={retain_res3['success']}, items={retain_res3['items_count']}")

    hindsight.close()
    print_separator("Milestone 2 Real Hindsight Test Completed Successfully")

if __name__ == "__main__":
    main()
