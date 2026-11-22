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

# API (Supabase). The anon key is public by design (it is in the web app's JS bundle),
# but it is still read from the environment so it can be rotated without code changes.
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://vtimmqlnyoyxiwczfdwf.supabase.co")
ANON_KEY = (os.getenv("DUMMYPAY_ANON_KEY")
            or os.getenv("SUPABASE_ANON_KEY")
            or "sb_publishable_ePbpDoNhaalSXl31_Rq6OA_TcfDZVAS")  # public key given in the assignment

AUTH_DIR = ROOT / ".auth"
