import re

from app.models import ContractData


def search(pattern: str, text: str):
    return re.search(pattern, text, re.IGNORECASE | re.DOTALL)


def analyse_contract_regex(text: str) -> ContractData:
    result = ContractData()

    match = search(
        r"(?:Supplier|Service Provider):\s*(.+?)(?:\r?\n|$)",
        text,
    )
    if match:
        result.supplier = match.group(1).strip()

    match = search(
        r"(?:Customer|Client):\s*(.+?)(?:\r?\n|$)",
        text,
    )
    if match:
        result.customer = match.group(1).strip()

    match = search(
        r"(?:contract term|initial term).*?(\d+)\s*months",
        text,
    )
    if match:
        result.term_months = int(match.group(1))

    match = search(
        r"(?:auto(?:matic)?[\s-]*renewal|automatically renews|renews for).*?(\d+)[\s-]*month",
        text,
    )
    if match:
        result.auto_renewal_months = int(match.group(1))

    match = search(r"payable within\s*(\d+)\s*days", text)
    if match:
        result.payment_terms_days = int(match.group(1))

    return result
