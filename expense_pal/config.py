import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.freeagent.com/v2"
TOKEN_PATH = Path.home() / ".config" / "expense-pal" / "tokens.json"
DESCRIPTIONS_FILE = Path.home() / ".config" / "expense-pal" / "descriptions.txt"
CALLBACK_URL = "http://localhost:8374/callback"
CALLBACK_PORT = 8374

CLIENT_ID = os.environ.get("FREEAGENT_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("FREEAGENT_CLIENT_SECRET", "")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-6")

_blacklist_raw = os.environ.get("EXPENSE_PAL_CATEGORY_BLACKLIST", "")
CATEGORY_BLACKLIST: set[str] = {
    code.strip() for code in _blacklist_raw.split(",") if code.strip()
}

EXPENSES_LOG = Path("expenses.jsonl")


def load_descriptions() -> list[str]:
    if not DESCRIPTIONS_FILE.exists():
        return []
    return [line for line in DESCRIPTIONS_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]


def save_description(desc: str):
    desc = desc.strip()
    if not desc:
        return
    existing = load_descriptions()
    if desc in existing:
        return
    DESCRIPTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with DESCRIPTIONS_FILE.open("a", encoding="utf-8") as f:
        f.write(desc + "\n")


def require_credentials():
    if not CLIENT_ID or not CLIENT_SECRET:
        print(
            "Error: FREEAGENT_CLIENT_ID and FREEAGENT_CLIENT_SECRET must be set.\n"
            "Copy .env.example to .env and fill in your credentials.",
            file=sys.stderr,
        )
        sys.exit(1)
