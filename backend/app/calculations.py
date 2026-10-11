from pydantic import BaseModel, Field

from app.models import ContractData


class FinancialInputs(BaseModel):
    monthly_mono_pages: int = Field(default=0, ge=0)
    monthly_colour_pages: int = Field(default=0, ge=0)


class FinancialAnalysis(BaseModel):
    currency: str | None = None
    annual_equipment_rental: float | None = None
    annual_base_fee: float | None = None
    annual_mono_cost: float | None = None
    annual_colour_cost: float | None = None
    annual_usage_cost: float | None = None
    calculated_annual_cost: float | None = None
    stated_annual_contract_value: float | None = None
    monthly_mono_pages: int = 0
    monthly_colour_pages: int = 0
    is_partial: bool = False
    notes: list[str] = []


def round_money(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 2)


def annualise_rental(amount: float | None, frequency: str | None) -> float | None:
    if amount is None or not frequency:
        return None

    multipliers = {
        "monthly": 12,
        "month": 12,
        "quarterly": 4,
        "quarter": 4,
        "annually": 1,
        "annual": 1,
        "yearly": 1,
        "year": 1,
    }

    multiplier = multipliers.get(frequency.strip().lower())
    if multiplier is None:
        return None
    return amount * multiplier


def calculate_channel_cost(
    monthly_pages: int,
    standard_cpc: float | None,
    overage_cpc: float | None,
    minimum_volume: int | None,
) -> tuple[float | None, bool]:
    if monthly_pages == 0:
        return 0.0, False

    if standard_cpc is not None:
        return monthly_pages * standard_cpc * 12, False

    if overage_cpc is not None and minimum_volume is not None:
        monthly_overage = max(0, monthly_pages - minimum_volume)
        return monthly_overage * overage_cpc * 12, False

    return None, True


def calculate_financials(
    contract: ContractData,
    inputs: FinancialInputs,
) -> FinancialAnalysis:
    notes: list[str] = []
    partial = False

    annual_rental = annualise_rental(
        contract.equipment_rental_gbp,
        contract.rental_frequency,
    )

    if contract.equipment_rental_gbp is not None and annual_rental is None:
        partial = True
        notes.append(
            "Equipment rental was found, but its payment frequency could not be annualised."
        )

    annual_base_fee = None
    if contract.monthly_base_fee_gbp is not None:
        annual_base_fee = contract.monthly_base_fee_gbp * 12

    mono_cost, mono_incomplete = calculate_channel_cost(
        monthly_pages=inputs.monthly_mono_pages,
        standard_cpc=contract.mono_cpc_gbp,
        overage_cpc=contract.mono_overage_cpc_gbp,
        minimum_volume=contract.minimum_mono_monthly,
    )

    colour_cost, colour_incomplete = calculate_channel_cost(
        monthly_pages=inputs.monthly_colour_pages,
        standard_cpc=contract.colour_cpc_gbp,
        overage_cpc=contract.colour_overage_cpc_gbp,
        minimum_volume=contract.minimum_colour_monthly,
    )

    if mono_incomplete:
        partial = True
        notes.append(
            "Mono usage was supplied but PrintSift does not have enough pricing information to calculate its cost."
        )

    if colour_incomplete:
        partial = True
        notes.append(
            "Colour usage was supplied but PrintSift does not have enough pricing information to calculate its cost."
        )

    usage_components = [value for value in [mono_cost, colour_cost] if value is not None]
    annual_usage_cost = sum(usage_components) if usage_components else None

    known_components = [
        value
        for value in [annual_rental, annual_base_fee, mono_cost, colour_cost]
        if value is not None
    ]
    calculated_annual_cost = sum(known_components) if known_components else None

    if contract.estimated_annual_contract_charge_gbp is not None:
        notes.append(
            "The contract also states an annual or Year 1 contract value. PrintSift keeps this separate from its calculated figure."
        )

    return FinancialAnalysis(
        currency=contract.currency,
        annual_equipment_rental=round_money(annual_rental),
        annual_base_fee=round_money(annual_base_fee),
        annual_mono_cost=round_money(mono_cost),
        annual_colour_cost=round_money(colour_cost),
        annual_usage_cost=round_money(annual_usage_cost),
        calculated_annual_cost=round_money(calculated_annual_cost),
        stated_annual_contract_value=round_money(
            contract.estimated_annual_contract_charge_gbp
        ),
        monthly_mono_pages=inputs.monthly_mono_pages,
        monthly_colour_pages=inputs.monthly_colour_pages,
        is_partial=partial,
        notes=notes,
    )
