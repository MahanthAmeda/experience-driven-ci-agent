import os
import sys
from dotenv import load_dotenv

# Load .env securely
load_dotenv()

# Environment mode switch: 'demo' vs 'development' (default)
APP_ENV = os.getenv("APP_ENV", "development").lower().strip()

HINDSIGHT_API_URL = os.getenv("HINDSIGHT_API_URL", "https://api.hindsight.vectorize.io")
HINDSIGHT_DEV_API_KEY = os.getenv("HINDSIGHT_DEV_API_KEY")
HINDSIGHT_DEMO_API_KEY = os.getenv("HINDSIGHT_DEMO_API_KEY")
HINDSIGHT_DEV_BANK_ID = os.getenv("HINDSIGHT_DEV_BANK_ID", "ci-agent-development")
HINDSIGHT_DEMO_BANK_ID = os.getenv("HINDSIGHT_DEMO_BANK_ID", "ci-agent-demo")

def get_config_for_mode(mode: str = None):
    """Resolve active bank, API key, local store, and forbidden banks based on mode."""
    env_mode = (mode or APP_ENV or "development").lower().strip()
    if env_mode == "demo":
        active_bank = HINDSIGHT_DEMO_BANK_ID
        active_key = HINDSIGHT_DEMO_API_KEY
        store_path = os.path.join("data", "demo_experiences.json")
        forbidden = {HINDSIGHT_DEV_BANK_ID}
    else:
        active_bank = HINDSIGHT_DEV_BANK_ID
        active_key = HINDSIGHT_DEV_API_KEY
        store_path = os.path.join("data", "experiences.json")
        forbidden = {HINDSIGHT_DEMO_BANK_ID}
    return active_bank, active_key, store_path, forbidden

ACTIVE_BANK_ID, ACTIVE_API_KEY, LOCAL_STORE_PATH, FORBIDDEN_BANKS = get_config_for_mode(APP_ENV)

# Safety guard: Prevent accidental writing to forbidden bank in current mode
if ACTIVE_BANK_ID in FORBIDDEN_BANKS:
    raise RuntimeError(
        f"SAFETY GUARD: Bank '{ACTIVE_BANK_ID}' is forbidden in {APP_ENV} mode!"
    )

