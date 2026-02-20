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
