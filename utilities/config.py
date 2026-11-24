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

SUPABASE_URL = "https://vtimmqlnyoyxiwczfdwf.supabase.co"
# Public API key given in the assignment (can be replaced through .env or a CI secret).
ANON_KEY = os.getenv("DUMMYPAY_ANON_KEY") or "sb_publishable_ePbpDoNhaalSXl31_Rq6OA_TcfDZVAS"

AUTH_DIR = ROOT / ".auth"
