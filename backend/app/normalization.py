from app.models import ContractData

INDEX_ALIASES = {
    "consumer prices index": "CPI",
    "consumer price index": "CPI",
    "cpi": "CPI",
    "retail prices index": "RPI",
    "retail price index": "RPI",
    "rpi": "RPI",
}


def normalize_contract(data: ContractData) -> ContractData:
    if data.annual_increase_index:
        lookup = data.annual_increase_index.strip().lower()
        data.annual_increase_index = INDEX_ALIASES.get(
            lookup, data.annual_increase_index
        )

    if data.rental_frequency:
        data.rental_frequency = data.rental_frequency.strip().lower()

    return data
