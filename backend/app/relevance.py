KEYWORDS = {
    "charges": 5,
    "pricing": 5,
    "price": 4,
    "payment": 4,
    "supplier": 4,
    "customer": 3,
    "commencement date": 5,
    "expiry date": 5,
    "contract period": 5,
    "schedule 3": 6,
    "charges, payment and invoicing": 8,
    "termination": 4,
    "renewal": 4,
    "extension": 3,
    "notice": 3,
    "cost per copy": 6,
    "cost per page": 6,
    "click charge": 6,
    "image charge": 6,
    "mono": 3,
    "colour": 3,
    "color": 3,
    "minimum volume": 5,
    "volume": 2,
    "cpi": 5,
    "rpi": 5,
    "index": 2,
    "increase": 2,
    "lease": 4,
    "rental": 4,
    "maintenance": 3,
    "service charge": 4,
}


def score_page(text: str) -> int:
    lower = text.lower()
    return sum(
        lower.count(keyword) * weight
        for keyword, weight in KEYWORDS.items()
    )


def select_relevant_pages(
    pages: list[str],
    max_pages: int = 25,
    front_pages: int = 10,
) -> list[tuple[int, str]]:
    selected_numbers = set()

    for page_number in range(1, min(front_pages, len(pages)) + 1):
        selected_numbers.add(page_number)

    scored = []
    for page_number, text in enumerate(pages, start=1):
        score = score_page(text)
        if score > 0:
            scored.append((score, page_number))

    scored.sort(reverse=True)

    for _, page_number in scored:
        if len(selected_numbers) >= max_pages:
            break
        selected_numbers.add(page_number)

    return [
        (page_number, pages[page_number - 1])
        for page_number in sorted(selected_numbers)
    ]


def format_selected_pages(pages: list[tuple[int, str]]) -> str:
    return "\n\n".join(
        f"=== PAGE {page_number} ===\n{text}"
        for page_number, text in pages
    )
