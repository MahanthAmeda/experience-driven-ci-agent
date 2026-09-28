# Experience-Driven CI Failure Resolution Agent

> An incident-resolution agent that remembers what worked — and what failed.
> *"Every resolved failure becomes experience for the next incident."*

---

## 1. Problem

CI/CD pipelines fail constantly due to flaky networks, package registry timeouts, dependency conflicts, runner misconfigurations, and environment drifts. 

Today, automated agents and developers treat every failure in isolation:
- They start from scratch without organizational memory.
- They repeatedly attempt naive fixes (e.g. blindly retrying an `npm install` when the registry route is down).
- They waste developer hours and cloud compute repeating mistakes that a teammate already solved yesterday.

---

## 2. Solution

The **Experience-Driven CI Failure Resolution Agent** uses [Hindsight Cloud](https://docs.dev.hindsight.vectorize.io/) to retain, recall, and synthesize empirical CI incident outcomes. 

Crucially, **the agent learns from action outcomes (`success` vs `failure`), not merely text similarity**:
1. When an engineer takes an action (e.g., retrying an install vs. switching registry configuration), the action, outcome result, resolution, and lesson learned are retained into Hindsight.
2. When a subsequent similar failure occurs, the agent recalls past attempts.
3. The agent's relevance layer filters out cross-domain noise (e.g. Python dependency issues when analyzing an npm registry timeout).
4. The learning engine compares what failed and what succeeded in the past, adapting its recommendation to prioritize the proven resolution and discommend ineffective attempts.

---

## 3. How Hindsight is Used

The agent leverages the official `hindsight-client` Python SDK (v0.10.1) for persistent agent memory:

- **`client.retain(bank_id, content, tags, metadata)`**:
  Retains structured incident narratives, action outcomes (`result:success` / `result:failure`), and lessons learned. Hindsight automatically extracts world facts, experience memories, and synthesized observations.
- **`client.recall(bank_id, query, budget="mid")`**:
  Executes TEMPR retrieval (combining semantic search, BM25 keyword matching, entity graph traversal, and temporal reasoning) to retrieve past incident memories.
- **`client.get_bank_config(bank_id)`**:
  Provides bank health checks and configuration validation.

---

## 4. Architecture

```
                                  +-----------------------------+
                                  |     CI Failure Incident     |
                                  |  (Repo, Signature, Logs)    |
                                  +-----------------------------+
                                                 |
                                [ Is Memory Enabled? ]
                                                / \
                                  No           /   \         Yes
                                              /     \
                +----------------------------+       +-----------------------------+
                |   Baseline Diagnostics     |       |   Hindsight TEMPR Recall    |
                | (Standard initial retry)   |       |   (Query by failure context)|
                +----------------------------+       +-----------------------------+
                              |                                     |
                              |                      +-----------------------------+
                              |                      |  Relevance Filtering Layer  |
                              |                      |  - Discards cross-domain    |
                              |                      |    noise (e.g. Python vs npm)
                              |                      |  - Scores contextual match  |
                              |                      +-----------------------------+
                              |                                     |
                              |                      +-----------------------------+
                              |                      |  Outcome Comparison Engine  |
                              |                      |  - Groups Actions by Result |
                              |                      |  - Compares Fail vs Success |
                              |                      +-----------------------------+
                              |                                     |
                              \                                     /
                               \                                   /
                +------------------------------------------------------------------+
                |                    Synthesized Recommendation                    |
                |  - Actionable recommendation based on empirical outcomes         |
                |  - "Why?" explanation detailing previous failed/successful tests |
                |  - Influencing experience references                             |
                +------------------------------------------------------------------+
```

---

## 5. Memory OFF vs Memory ON

The system demonstrates a genuine behavioral difference between modes:

| Dimension | Memory OFF | Memory ON |
| :--- | :--- | :--- |
| **API Parameter** | `memory_enabled: false` | `memory_enabled: true` |
| **Hindsight Call** | `recall()` is **never called** | `recall()` queries the memory bank |
| **Analysis Basis** | Static first-principles baseline diagnostics | Historical outcome intelligence & empirical trial results |
| **Recommendation** | Recommends standard naive initial retry | Recommends proven fix, warns against past failed actions |
| **Reasoning** | Explains that memory is disabled | Explains empirical evidence comparing past successes and failures |

---

## 6. Experience Learning Flow

The agent demonstrates an empirical 3-stage learning progression:

```
[Experience 1]
Failure: npm_install_timeout (ETIMEDOUT to registry.npmjs.org)
Action Taken: Retry npm install
Outcome: FAILED (Repeated retries ineffective when registry route is down)
      ↓
[Experience 2]
Failure: Similar npm_install_timeout
Agent Recall: Recalls Experience 1 retry failure -> Adapts recommendation away from retrying!
Action Taken: Verified npm registry configuration & switched to accessible mirror
Outcome: SUCCESS
      ↓
[Experience 3]
Failure: Subsequent npm_install_timeout
Agent Recall: Recalls both Experience 1 (Retry: FAILED) and Experience 2 (Registry Fix: SUCCESS)
Agent Recommendation: Directly prioritizes registry configuration fix and warns against retry!
Outcome: SUCCESS
```

---

## 7. Environment Variables

Create or maintain a `.env` file in the project root:

```ini
HINDSIGHT_API_URL=https://api.hindsight.vectorize.io
HINDSIGHT_DEV_API_KEY=your_development_api_key_here
HINDSIGHT_DEMO_API_KEY=your_demo_api_key_here
HINDSIGHT_DEV_BANK_ID=ci-agent-development
HINDSIGHT_DEMO_BANK_ID=ci-agent-demo
```

> **Security Note:**  
> API keys must **always** remain in `.env` and must **never** be committed to version control. The `.gitignore` file is strictly configured to ignore `.env` and `.env.*`.

---

## 8. Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### Backend Setup
```bash
# 1. Create and activate virtual environment
python -m venv .venv

# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# 2. Install dependencies
pip install hindsight-client python-dotenv fastapi uvicorn pytest httpx
```

### Frontend Setup
```bash
cd frontend
npm install
npm run build
cd ..
```

---

## 9. Running the Application

### Option A: Unified Full-Stack Server (FastAPI + Built Frontend)
Start the FastAPI server; it automatically serves both the REST API and the built React frontend:

```bash
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

### Option B: Development Mode (Vite Hot-Reload + FastAPI)
In Terminal 1 (Backend):
```bash
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
In Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)** in your browser (API calls are proxied to port 8000).

---

## 10. Running Automated Tests

Run the complete backend test suite:
```bash
.\.venv\Scripts\python.exe -m pytest -v tests
```

Tests cover:
- **`test_memory_modes.py`**: Verifies `recall()` is never called when Memory is OFF; verifies `recall()` is called when Memory is ON.
- **`test_relevance_filtering.py`**: Verifies cross-domain memories (e.g. Python dependency failure) are tagged "Low relevance" and excluded from npm recommendations.
- **`test_learning_progression.py`**: Verifies recommendations adapt dynamically across Experience 1, 2, and 3 states based on outcome data.
- **`test_experience_storage.py`**: Verifies experience persistence and outcome lifecycle updates.
- **`test_api_endpoints.py`**: Verifies all REST API endpoints (`/api/health`, `/api/analyse`, `/api/experience`, `/api/experiences`, `/api/experiences/{id}/outcome`).

Run end-to-end integration verification:
```bash
.\.venv\Scripts\python.exe verify_e2e_ui_api.py
```

---

## 11. Demo Flow (2–3 Minutes)

1. **Step 1: Baseline (Memory OFF)**
   - Click "Scenario 1: Baseline (Memory OFF)".
   - Click **Analyse Failure**.
   - Result: Baseline diagnostic recommendation ("Retry the npm installation once and verify registry/network connectivity").
   - Notice: "Memory disabled — recommendation uses only current failure."

2. **Step 2: Experience 1 Influence (Memory ON)**
   - Click "Scenario 2: Learn from Failed Retry" (turns Memory ON).
   - Click **Analyse Failure**.
   - Result: Hindsight recalls Experience 1 where retrying resulted in **FAILURE**.
   - Notice: Recommendation dynamically changes to **"Do NOT repeatedly retry npm install... investigate registry configuration"**.

3. **Step 3: Outcome Comparison (Memory ON)**
   - Click "Scenario 3: Prioritize Proven Fix".
   - Click **Analyse Failure**.
   - Result: Hindsight recalls both Experience 1 (Retry -> FAILED) and Experience 2 (Registry Configuration -> SUCCESS).
   - Notice: Recommendation synthesizes both outcomes, prioritizing the proven registry resolution and warning against naive retries.

4. **Step 4: Record Outcome & Update Hindsight**
   - In the "Record Engineer Action & Outcome" form, select **Success** or **Failed**.
   - Click **Save Experience to Hindsight**.
   - Experience is retained into the development bank and immediately appears in the **Experience Progression Timeline**.

---

## 12. Demo Bank Safety Policy

- **`ci-agent-demo`** is strictly reserved and never touched during automated testing or development.
- All testing and progression demonstrations run exclusively against **`ci-agent-development`**.
- Safety guards in `app/config.py` enforce this boundary at the application level.
