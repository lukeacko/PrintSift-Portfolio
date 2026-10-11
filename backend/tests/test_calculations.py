from app.calculations import FinancialInputs, annualise_rental, calculate_financials
from app.models import ContractData


def test_annualise_quarterly_rental():
    assert annualise_rental(250.0, "quarterly") == 1000.0


def test_calculate_financials_with_simple_cpc():
    contract = ContractData(
        currency="GBP",
        equipment_rental_gbp=300.0,
        rental_frequency="quarterly",
        mono_cpc_gbp=0.01,
        colour_cpc_gbp=0.05,
    )

    result = calculate_financials(
        contract,
        FinancialInputs(
            monthly_mono_pages=10_000,
            monthly_colour_pages=1_000,
        ),
    )

    assert result.annual_equipment_rental == 1200.0
    assert result.annual_mono_cost == 1200.0
    assert result.annual_colour_cost == 600.0
    assert result.calculated_annual_cost == 3000.0
    assert result.is_partial is False
