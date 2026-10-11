from pydantic import BaseModel


class ContractData(BaseModel):
    # Document / parties
    document_type: str | None = None
    supplier: str | None = None
    customer: str | None = None
    finance_provider: str | None = None
    currency: str | None = None

    # Dates / term
    agreement_date: str | None = None
    effective_date: str | None = None
    installation_date: str | None = None
    term_months: int | None = None
    expiry_date: str | None = None
    extension_expiry_date: str | None = None

    # Equipment rental
    equipment_rental_gbp: float | None = None
    rental_frequency: str | None = None

    # Service
    monthly_base_fee_gbp: float | None = None

    # Print charges
    mono_cpc_gbp: float | None = None
    colour_cpc_gbp: float | None = None
    mono_overage_cpc_gbp: float | None = None
    colour_overage_cpc_gbp: float | None = None
    minimum_mono_monthly: int | None = None
    minimum_colour_monthly: int | None = None
    estimated_annual_contract_charge_gbp: float | None = None

    # Escalation
    annual_increase_description: str | None = None
    annual_increase_fixed_percent: float | None = None
    annual_increase_floor_percent: float | None = None
    annual_increase_cap_percent: float | None = None
    annual_increase_index: str | None = None
    annual_increase_margin_percent: float | None = None

    # Renewal / notice
    non_renewal_notice_days: int | None = None
    extension_notice_days: int | None = None
    termination_notice_days: int | None = None
    termination_notice_working_days: int | None = None
    auto_renewal_months: int | None = None
    notice_window_start_days: int | None = None
    notice_window_end_days: int | None = None

    # Termination
    early_termination_description: str | None = None
    equipment_collection_fee_gbp: float | None = None

    # Payment
    payment_terms_days: int | None = None


class EvidenceItem(BaseModel):
    field: str
    page: int
    quote: str


class AIExtractionResult(BaseModel):
    data: ContractData
    evidence: list[EvidenceItem]
