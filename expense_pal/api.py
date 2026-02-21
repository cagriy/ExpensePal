import requests

from expense_pal.config import BASE_URL


def list_expenses(token: str, per_page: int = 10) -> list[dict]:
    """Fetch recent expenses from FreeAgent."""
    resp = requests.get(
        f"{BASE_URL}/expenses",
        params={"view": "recent", "per_page": per_page},
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
    )
    resp.raise_for_status()
    return resp.json().get("expenses", [])


def fetch_expense_descriptions(token: str, total: int = 200) -> list[str]:
    """Fetch up to `total` expenses and return deduplicated non-blank descriptions."""
    per_page = 100
    pages = (total + per_page - 1) // per_page
    seen: dict[str, None] = {}
    for page in range(1, pages + 1):
        resp = requests.get(
            f"{BASE_URL}/expenses",
            params={"view": "recent", "per_page": per_page, "page": page},
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
        )
        resp.raise_for_status()
        expenses = resp.json().get("expenses", [])
        if not expenses:
            break
        for exp in expenses:
            desc = (exp.get("description") or "").strip()
            if desc and desc not in seen:
                seen[desc] = None
    return list(seen.keys())
