"""Central configuration. Secrets come from .env (local) or CI secrets - never hard-coded."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

BASE_URL = os.getenv("BASE_URL", "https://dummypay.vercel.app")
USER1_EMAIL = os.getenv("USER1_EMAIL", "")
USER1_PASSWORD = os.getenv("USER1_PASSWORD", "")
USER2_EMAIL = os.getenv("USER2_EMAIL", "")
USER2_PASSWORD = os.getenv("USER2_PASSWORD", "")

AUTH_DIR = ROOT / ".auth"
