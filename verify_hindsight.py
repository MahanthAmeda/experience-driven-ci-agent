"""
Verification script for Hindsight connectivity and memory operations.
"""

import os
import sys
from dotenv import load_dotenv
from hindsight_client import Hindsight

def main():
    # Load environment variables securely from .env
    load_dotenv()

    api_url = os.getenv("HINDSIGHT_API_URL")
    dev_api_key = os.getenv("HINDSIGHT_DEV_API_KEY")
    bank_id = "ci-agent-development"

    if not api_url:
        print("ERROR: HINDSIGHT_API_URL is missing in environment/.env", file=sys.stderr)
        sys.exit(1)

    if not dev_api_key:
        print("ERROR: HINDSIGHT_DEV_API_KEY is missing in environment/.env", file=sys.stderr)
        sys.exit(1)

    print(f"Connecting to Hindsight API URL: {api_url}")
    print(f"Target Bank ID: {bank_id}")
    print("API key loaded: [REDACTED - PRESENT]")

    # Initialize client
    client = Hindsight(base_url=api_url, api_key=dev_api_key)

    try:
        # Step 1: Verify bank accessibility
        print("\n--- Step 1: Verifying bank accessibility ---")
        config = client.get_bank_config(bank_id=bank_id)
        print(f"Bank configuration retrieved successfully for: {bank_id}")

        # Step 2: Perform retain operation
        print("\n--- Step 2: Retain test experience ---")
        test_experience = (
            "Development verification test: A Python package installation failed because of a "
            "dependency conflict. The engineer resolved the issue by pinning compatible package versions. "
            "The fix succeeded. Lesson: check dependency compatibility before retrying installation."
        )
        
        # Verify retain behavior (synchronous by default, retain_async=False)
        print("Executing retain() with default parameters (synchronous by default)...")
        retain_resp = client.retain(
            bank_id=bank_id,
            content=test_experience
        )

        is_async = getattr(retain_resp, "var_async", False)
        op_id = getattr(retain_resp, "operation_id", None)
        success = getattr(retain_resp, "success", False)
        items_count = getattr(retain_resp, "items_count", 0)

        print(f"Retain status: success={success}, async={is_async}, items_count={items_count}")
        if op_id:
            print(f"Operation ID: {op_id}")

        # If async processing is ever indicated, handle using official get_operation_status
        if is_async and op_id:
            print("Operation processed asynchronously. Checking operation status...")
            op_status = client.operations.get_operation_status(bank_id=bank_id, operation_id=op_id)
            print(f"Operation status: {getattr(op_status, 'status', 'unknown')}")

        # Step 3: Perform recall query
        print("\n--- Step 3: Recall query ---")
        recall_query = "What happened in the previous Python dependency installation failure, and what fixed it?"
        print(f"Executing recall() with query: '{recall_query}'")

        recall_resp = client.recall(
            bank_id=bank_id,
            query=recall_query
        )

        results = getattr(recall_resp, "results", [])
        print(f"Recall completed. Results count: {len(results)}")

        matched_test_memory = False
        for idx, res in enumerate(results, 1):
            text = getattr(res, "text", "")
            mem_type = getattr(res, "type", "unknown")
            print(f"Result #{idx} [{mem_type}]: {text}")
            if "dependency conflict" in text or "Python package installation" in text:
                matched_test_memory = True

        if matched_test_memory:
            print("\nSUCCESS: Retained test experience was successfully recalled!")
        else:
            print("\nNOTE: Results returned, but expected match criteria was not met.")

    finally:
        client.close()
        print("\nClient connection closed cleanly.")

if __name__ == "__main__":
    main()
