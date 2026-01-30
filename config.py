"""
GRAVITYbot Configuration
------------------------
Centralized configuration loaded from environment variables.
"""
import os
import pathlib

import dotenv

# Load .env file
dotenv.load_dotenv(dotenv.find_dotenv())


def _get_project_root():
    """Determine project root from this file's location."""
    # config.py lives in project root
    return pathlib.Path(__file__).resolve().parent


PROJECT_ROOT = _get_project_root()

# ---------------------
# Dry Run Mode
# ---------------------
# When True: runs full pipeline (fetch data, generate summaries) but skips:
#   - Sending emails
#   - Posting to Zooniverse Talk forums
# ---------------------
DRY_RUN = os.environ.get("GRAVITYBOT_DRY_RUN", "false").lower() == "true"

# ---------------------
# Folder Paths
# ---------------------
DATA_FOLDER_PATH = pathlib.Path(
    os.environ.get("GRAVITYBOT_DATA_FOLDER_PATH", str(PROJECT_ROOT / "_data"))
)
OUTPUT_FOLDER_PATH = pathlib.Path(
    os.environ.get("GRAVITYBOT_OUTPUT_FOLDER_PATH", str(PROJECT_ROOT / "_output"))
)

# ---------------------
# Azure OpenAI
# ---------------------
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21")
AZURE_OPENAI_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

# ---------------------
# LLM Defaults
# ---------------------
LLM_TEMPERATURE = float(os.environ.get("GRAVITYBOT_LLM_TEMPERATURE", "0.8"))
LLM_MAX_TOKENS = int(os.environ.get("GRAVITYBOT_LLM_MAX_TOKENS", "4096"))

# ---------------------
# Panoptes / Zooniverse
# ---------------------
PANOPTES_SLUG = os.environ.get("PANOPTES_SLUG", "zooniverse/gravity-spy")
PANOPTES_USER = os.environ.get("PANOPTES_USER")
PANOPTES_PASS = os.environ.get("PANOPTES_PASS")
PANOPTES_ID = os.environ.get("PANOPTES_ID")

# ---------------------
# SMTP / Email
# ---------------------
SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
SMTP_FROM = os.environ.get("SMTP_FROM")
SMTP_TO = os.environ.get("SMTP_TO")


def print_config():
    """Print current configuration (for debugging). Redacts sensitive values."""
    def _redact(val):
        if val and len(val) > 4:
            return val[:4] + "..." 
        return "[not set]" if not val else val
    
    print("GRAVITYbot Configuration")
    print("=" * 40)
    print(f"DRY_RUN: {DRY_RUN}")
    print(f"DATA_FOLDER_PATH: {DATA_FOLDER_PATH}")
    print(f"OUTPUT_FOLDER_PATH: {OUTPUT_FOLDER_PATH}")
    print()
    print("Azure OpenAI:")
    print(f"  ENDPOINT: {AZURE_OPENAI_ENDPOINT}")
    print(f"  DEPLOYMENT: {AZURE_OPENAI_DEPLOYMENT}")
    print(f"  API_VERSION: {AZURE_OPENAI_API_VERSION}")
    print(f"  API_KEY: {_redact(AZURE_OPENAI_API_KEY)}")
    print()
    print("Panoptes:")
    print(f"  SLUG: {PANOPTES_SLUG}")
    print(f"  USER: {PANOPTES_USER}")
    print(f"  ID: {PANOPTES_ID}")
    print()
    print("SMTP:")
    print(f"  HOST: {SMTP_HOST}")
    print(f"  FROM: {SMTP_FROM}")
    print(f"  TO: {SMTP_TO}")