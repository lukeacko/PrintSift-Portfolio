import re

from app.models import EvidenceItem


def normalise_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def validate_evidence(
    pages: list[str],
    evidence: list[EvidenceItem],
) -> list[dict]:
    results = []

    for item in evidence:
        page_index = item.page - 1

        if page_index < 0 or page_index >= len(pages):
            results.append(
                {
                    "field": item.field,
                    "valid": False,
                    "reason": "Invalid page number",
                }
            )
            continue

        page_text = normalise_text(pages[page_index])
        quote = normalise_text(item.quote)
        quote_found = quote in page_text

        results.append(
            {
                "field": item.field,
                "page": item.page,
                "quote": item.quote,
                "valid": quote_found,
                "reason": None if quote_found else "Quote not found on supplied page",
            }
        )

    return results
