import base64
import json
import sys
from pathlib import Path

import anthropic

from expense_pal.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from expense_pal.categories import get_llm_category_names
from expense_pal.prompts.receipt_extraction import SYSTEM_PROMPT, build_user_prompt

SUPPORTED_IMAGE_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
SUPPORTED_TYPES = set(SUPPORTED_IMAGE_TYPES.keys()) | {".pdf"}


def scan_receipt(file_path: Path) -> dict:
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
    prompt = build_user_prompt(category_list)
    system_prompt = SYSTEM_PROMPT

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=ANTHROPIC_MODEL,
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
