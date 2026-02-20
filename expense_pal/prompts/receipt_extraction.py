SYSTEM_PROMPT = (
    "You are a receipt and invoice data extraction assistant. "
    "Extract structured data from receipts and invoices and return it as JSON. "
    "Always return valid JSON only, with no surrounding text or markdown."
)


def build_user_prompt(category_list: str) -> str:
    return (
        "Extract the following from this receipt/invoice and return ONLY valid JSON:\n"
        '- "date": date in YYYY-MM-DD format\n'
        '- "total_amount": total amount paid as a string (e.g. "45.50")\n'
        '- "vat_amount": VAT/tax amount as a string (e.g. "7.58"), or "0.00" if not shown\n'
        f'- "category": one of the following categories that best matches: {category_list}\n\n'
        "Return ONLY the JSON object, no other text."
    )
