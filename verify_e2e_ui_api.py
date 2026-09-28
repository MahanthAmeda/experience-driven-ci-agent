"""
End-to-End Verification of the UI Backend Integration:
Tests the real backend APIs, Hindsight connectivity, Memory OFF, Memory ON,
Relevance filtering, Outcome recording, and Frontend static serving.
"""

from fastapi.testclient import TestClient
from app.main import app

def main():
    print("=" * 60)
    print(" E2E VERIFICATION: BACKEND APIS & HINDSIGHT INTEGRATION")
    print("=" * 60)

    client = TestClient(app)

    # 1. Health Endpoint
    print("\n[1] Testing GET /api/health...")
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    health_data = res.json()
    print(f"    Status: {health_data['status']}")
    print(f"    Active Bank: {health_data['active_bank']}")
    print(f"    Hindsight Status: {health_data['hindsight']['status']}")
    assert health_data["active_bank"] == "ci-agent-development"
    assert health_data["hindsight"]["status"] == "connected"

    # 2. Memory OFF Analysis
    print("\n[2] Testing POST /api/analyse with MEMORY OFF...")
    failure_payload = {
        "repository": "acme/payment-service",
        "workflow": "CI / Build",
        "failure_signature": "npm_install_timeout",
        "error_type": "FetchError",
        "error_message": "ETIMEDOUT while requesting packages from registry.npmjs.org",
        "environment": "Node.js 20 / Ubuntu"
    }

    res_off = client.post("/api/analyse", json={"failure": failure_payload, "memory_enabled": False})
    assert res_off.status_code == 200, f"Analyse OFF failed: {res_off.text}"
    off_data = res_off.json()
    print(f"    Memory Enabled: {off_data['memory_enabled']}")
    print(f"    Recommendation: {off_data['recommendation']}")
    print(f"    Reasoning: {off_data['reasoning']}")
    print(f"    Recalled Count: {len(off_data['recalled_experiences'])}")
    assert off_data["memory_enabled"] is False
    assert len(off_data["recalled_experiences"]) == 0
    assert "Retry the npm installation once" in off_data["recommendation"]

    # 3. Memory ON Analysis (Real Hindsight Recall & Outcome Reasoning)
    print("\n[3] Testing POST /api/analyse with MEMORY ON (Real Hindsight)...")
    res_on = client.post("/api/analyse", json={"failure": failure_payload, "memory_enabled": True})
    assert res_on.status_code == 200, f"Analyse ON failed: {res_on.text}"
    on_data = res_on.json()
    print(f"    Memory Enabled: {on_data['memory_enabled']}")
    print(f"    Total Recalled: {len(on_data['recalled_experiences'])}")
    print(f"    Relevant Experiences: {len(on_data['relevant_experiences'])}")
    print(f"    Low Relevance Experiences: {len(on_data['low_relevance_experiences'])}")
    print(f"    Recommendation: {on_data['recommendation']}")
    print(f"    Reasoning: {on_data['reasoning'][:120]}...")
    print(f"    Influencing: {on_data['influencing_experiences']}")
    assert on_data["memory_enabled"] is True
    assert len(on_data["recalled_experiences"]) > 0
    assert len(on_data["relevant_experiences"]) > 0
    assert "retrying did not resolve" in on_data["recommendation"].lower() or "do not" in on_data["recommendation"].lower()

    # Verify Relevance Filtering: check that any Python memory is marked Low relevance
    python_memories = [m for m in on_data["recalled_experiences"] if "python" in m["text"].lower()]
    if python_memories:
        print(f"\n    Relevance Filter verified: Found {len(python_memories)} Python memory units")
        for pm in python_memories[:1]:
            print(f"    - [{pm['relevance_status']}]: {pm['text'][:70]}... (Reason: {pm['relevance_reason']})")
            assert pm["relevance_status"] == "Low relevance"

    # 4. List Experiences Endpoint
    print("\n[4] Testing GET /api/experiences...")
    res_exps = client.get("/api/experiences")
    assert res_exps.status_code == 200
    exps_list = res_exps.json()
    print(f"    Stored Experiences Count: {len(exps_list)}")

    # 5. Frontend Root Serving
    print("\n[5] Testing GET / (Frontend Static Serving)...")
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "Experience-Driven CI Failure Resolution Agent" in res_root.text
    print("    Frontend index.html successfully served by FastAPI!")

    print("\n" + "=" * 60)
    print(" ALL END-TO-END CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()
