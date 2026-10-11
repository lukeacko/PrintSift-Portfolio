from app.models import EvidenceItem
from app.validation import validate_evidence


def test_evidence_quote_is_verified_on_correct_page():
    pages = [
        "Supplier: Example Print Ltd\nContract term: 60 months",
        "Colour cost per page is 0.05 GBP.",
    ]

    evidence = [
        EvidenceItem(
            field="supplier",
            page=1,
            quote="Supplier: Example Print Ltd",
        ),
        EvidenceItem(
            field="colour_cpc_gbp",
            page=2,
            quote="Colour cost per page is 0.05 GBP.",
        ),
    ]

    results = validate_evidence(pages, evidence)
    assert [item["valid"] for item in results] == [True, True]


def test_wrong_page_is_not_verified():
    pages = ["Supplier: Example Print Ltd", "Other wording"]
    evidence = [
        EvidenceItem(
            field="supplier",
            page=2,
            quote="Supplier: Example Print Ltd",
        )
    ]

    assert validate_evidence(pages, evidence)[0]["valid"] is False
