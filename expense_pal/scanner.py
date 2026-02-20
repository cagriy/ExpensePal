import base64
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import anthropic

from expense_pal.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from expense_pal.categories import get_llm_category_names

_PROMPTS_FILE = Path(__file__).parent / "prompts" / "receipt_extraction.md"


def _load_prompts() -> tuple[str, str]:
    text = _PROMPTS_FILE.read_text()
    system = re.search(r"## System Prompt\n\n(.+?)(?=\n## |\Z)", text, re.DOTALL).group(1).strip()
    user = re.search(r"## User Prompt\n\n(.+?)(?=\n## |\Z)", text, re.DOTALL).group(1).strip()
    return system, user

SUPPORTED_IMAGE_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
SUPPORTED_TYPES = set(SUPPORTED_IMAGE_TYPES.keys()) | {".pdf"}


def scan_receipt(file_path: Path, model: str | None = None) -> dict:
    """Send a receipt image or PDF to Claude for extraction and classification.

    Returns a dict with keys: date, total_amount, vat_amount, category.
    """
    ext = file_path.suffix.lower()
    if ext not in SUPPORTED_TYPES:
        print(f"Error: unsupported file type '{ext}'. Supported: {', '.join(sorted(SUPPORTED_TYPES))}", file=sys.stderr)
        sys.exit(1)

    data = base64.standard_b64encode(file_path.read_bytes()).decode("utf-8")

    if ext in SUPPORTED_IMAGE_TYPES:
        media_type = SUPPORTED_IMAGE_TYPES[ext]
        file_block = {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": data,
            },
        }
    else:
        file_block = {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": data,
            },
        }

    category_list = ", ".join(get_llm_category_names())
    system_prompt, user_prompt_template = _load_prompts()
    prompt = user_prompt_template.format(category_list=category_list)

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{timestamp}_prompt.txt"
    log_file.write_text(f"=== System Prompt ===\n{system_prompt}\n\n=== User Prompt ===\n{prompt}\n")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=model or ANTHROPIC_MODEL,
        max_tokens=512,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": [
                    file_block,
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    result = json.loads(raw)

    # Normalise keys with defaults
    return {
        "date": result.get("date", ""),
        "total_amount": result.get("total_amount", "0.00"),
        "vat_amount": result.get("vat_amount", "0.00"),
        "category": result.get("category", ""),
    }
