from expense_pal.config import CATEGORY_BLACKLIST

_ADMIN_EXPENSES_CATEGORIES = [
    {"nominal_code": "201", "description": "Accountancy Fees"},
    {"nominal_code": "285", "description": "Accommodation and Meals"},
    {"nominal_code": "220", "description": "Advertising and Promotions"},
    {"nominal_code": "202", "description": "Bank Charges"},
    {"nominal_code": "203", "description": "Books and Publications"},
    {"nominal_code": "204", "description": "Cleaning"},
    {"nominal_code": "290", "description": "Client Entertainment"},
    {"nominal_code": "440", "description": "Computer Software"},
    {"nominal_code": "441", "description": "Hardware and Equipment"},
    {"nominal_code": "209", "description": "Insurance"},
    {"nominal_code": "211", "description": "Legal and Professional Fees"},
    {"nominal_code": "453", "description": "Motor Expenses"},
    {"nominal_code": "215", "description": "Office Expenses"},
    {"nominal_code": "207", "description": "Postage and Couriers"},
    {"nominal_code": "208", "description": "Printing and Stationery"},
    {"nominal_code": "410", "description": "Rent and Rates"},
    {"nominal_code": "460", "description": "Subscriptions"},
    {"nominal_code": "430", "description": "Telephone and Internet"},
    {"nominal_code": "210", "description": "Training"},
    {"nominal_code": "213", "description": "Travel and Transport"},
    {"nominal_code": "420", "description": "Utilities"},
    {"nominal_code": "500", "description": "Wages and Salaries"},
]

_COST_OF_SALES_CATEGORIES = [
    {"nominal_code": "100", "description": "Direct Labour"},
    {"nominal_code": "101", "description": "Materials"},
    {"nominal_code": "102", "description": "Subcontractors"},
    {"nominal_code": "103", "description": "Equipment Hire"},
    {"nominal_code": "104", "description": "Cost of Sales - Other"},
]

_ALL_CATEGORIES = _ADMIN_EXPENSES_CATEGORIES + _COST_OF_SALES_CATEGORIES


def get_all_categories() -> list[dict]:
    """Return all categories (for the TUI Select widget, includes blacklisted ones)."""
    return _ALL_CATEGORIES


def get_llm_categories() -> list[dict]:
    """Return categories minus blacklisted ones (for the LLM prompt)."""
    return [c for c in _ALL_CATEGORIES if c["nominal_code"] not in CATEGORY_BLACKLIST]


def get_llm_category_names() -> list[str]:
    """Return just the descriptions from LLM-eligible categories, for building the prompt."""
    return [c["description"] for c in get_llm_categories()]


def get_nominal_code(description: str) -> str | None:
    """Look up nominal code by category description."""
    for cat in _ALL_CATEGORIES:
        if cat["description"] == description:
            return cat["nominal_code"]
    return None
