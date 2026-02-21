import argparse
import json
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from expense_pal.config import ANTHROPIC_API_KEY, DESCRIPTIONS_FILE, EXPENSES_LOG, require_credentials, save_description
from expense_pal.auth import get_access_token
from expense_pal.api import fetch_expense_descriptions, list_expenses

SUPPORTED_SCAN_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}


def cmd_list(args):
    require_credentials()
    token = get_access_token()
    expenses = list_expenses(token)

    if not expenses:
        print("No expenses found.")
        return

    header = f"{'Date':<12} {'Description':<40} {'Amount':>10} {'Currency':<5}"
    print(header)
    print("-" * len(header))
    for exp in expenses:
        date = exp.get("dated_on", "")
        desc = exp.get("description", "")[:40]
        gross = exp.get("gross_value", "")
        currency = exp.get("currency", "")
        print(f"{date:<12} {desc:<40} {gross:>10} {currency:<5}")


def cmd_sync_descriptions(args):
    require_credentials()
    token = get_access_token()
    descriptions = fetch_expense_descriptions(token, total=200)
    DESCRIPTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    DESCRIPTIONS_FILE.write_text("\n".join(descriptions) + ("\n" if descriptions else ""), encoding="utf-8")
    print(f"Saved {len(descriptions)} descriptions to {DESCRIPTIONS_FILE}")


def cmd_scan(args):
    from expense_pal.scanner import scan_receipt
    from expense_pal.web_review import review_receipt
    from expense_pal.categories import get_all_categories, get_nominal_code

    file_path = Path(args.file).resolve()

    if not file_path.exists():
        print(f"Error: file not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    if file_path.suffix.lower() not in SUPPORTED_SCAN_EXTENSIONS:
        print(
            f"Error: unsupported file type '{file_path.suffix}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_SCAN_EXTENSIONS))}",
            file=sys.stderr,
        )
        sys.exit(1)

    if not ANTHROPIC_API_KEY:
        print(
            "Error: ANTHROPIC_API_KEY is not set.\n"
            "Add it to your .env file or export it in your shell.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Scanning {file_path.name} with Claude...")
    extracted = scan_receipt(file_path)
    print(f"Extracted: {extracted}")

    categories = get_all_categories()
    confirmed = review_receipt(extracted, categories, file_path)

    if confirmed is None:
        print("Cancelled — nothing saved.")
        return

    # Look up nominal code for the chosen category
    nominal_code = get_nominal_code(confirmed["category"]) or ""

    entry = {
        "date": confirmed["date"],
        "total_amount": confirmed["total_amount"],
        "vat_amount": confirmed["vat_amount"],
        "category": confirmed["category"],
        "category_nominal_code": nominal_code,
        "description": confirmed["description"],
        "source_file": str(file_path),
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    with EXPENSES_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    save_description(confirmed["description"])
    print(f"Saved to {EXPENSES_LOG}")


def cmd_multi_scan(args):
    from expense_pal.web_review import review_receipts_batch
    from expense_pal.categories import get_all_categories

    folder = Path(args.folder).resolve()

    if not folder.exists():
        print(f"Error: folder not found: {folder}", file=sys.stderr)
        sys.exit(1)

    if not folder.is_dir():
        print(f"Error: not a directory: {folder}", file=sys.stderr)
        sys.exit(1)

    if not ANTHROPIC_API_KEY:
        print(
            "Error: ANTHROPIC_API_KEY is not set.\n"
            "Add it to your .env file or export it in your shell.",
            file=sys.stderr,
        )
        sys.exit(1)

    pending = sorted(
        f.name for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_SCAN_EXTENSIONS
    )
    if not pending:
        print(f"No supported receipt files found in {folder}")
        print(f"Supported formats: {', '.join(sorted(SUPPORTED_SCAN_EXTENSIONS))}")
        return

    print(f"Found {len(pending)} receipt(s) in {folder}")
    categories = get_all_categories()
    confirmed = review_receipts_batch(folder, categories, train=args.train)
    print(f"\nProcessed {len(confirmed)} receipt(s).")
    if confirmed:
        print(f"Saved to {EXPENSES_LOG}")


def main():
    parser = argparse.ArgumentParser(prog="expense-pal", description="FreeAgent expense manager")
    parser.add_argument("--version", action="version", version=f"%(prog)s {version('expense-pal')}")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("list", help="List recent expenses")

    scan_parser = sub.add_parser("scan", help="Scan a receipt or invoice with Claude")
    scan_parser.add_argument("file", help="Path to receipt image (.jpg, .png) or PDF (.pdf)")

    multi_scan_parser = sub.add_parser("multi-scan", help="Batch-process receipts from a folder")
    multi_scan_parser.add_argument(
        "folder",
        nargs="?",
        default="receipts",
        help="Folder containing receipts (default: receipts/)",
    )
    multi_scan_parser.add_argument(
        "--train",
        action="store_true",
        default=False,
        help="Show inline prompt editor for iterating on the extraction prompt",
    )

    sub.add_parser("sync-descriptions", help="Sync expense descriptions from FreeAgent")

    args = parser.parse_args()
    if args.command == "list":
        cmd_list(args)
    elif args.command == "scan":
        cmd_scan(args)
    elif args.command == "multi-scan":
        cmd_multi_scan(args)
    elif args.command == "sync-descriptions":
        cmd_sync_descriptions(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
