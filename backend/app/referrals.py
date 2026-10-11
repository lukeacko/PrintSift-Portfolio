import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import insert, select, update as sql_update

from app.database import engine, initialise_database, referrals_table


REFERRAL_STATUSES = (
    "new",
    "contacted",
    "qualified",
    "supplier_search",
    "awaiting_approval",
    "introduced",
    "quoted",
    "won",
    "lost",
)


class ReferralRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=200)
    contact_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=40)
    postcode: str | None = Field(default=None, max_length=20)
    change_timing: str | None = Field(default=None, max_length=50)
    priorities: list[str] = Field(default_factory=list, max_length=12)
    current_supplier: str | None = Field(default=None, max_length=200)
    current_annual_cost: float | None = Field(default=None, ge=0, le=1_000_000_000)
    currency: str | None = Field(default=None, max_length=3)
    contract_expiry: str | None = Field(default=None, max_length=100)
    contract_type: str | None = Field(default=None, max_length=100)
    monthly_mono_pages: int | None = Field(default=None, ge=0, le=100_000_000)
    monthly_colour_pages: int | None = Field(default=None, ge=0, le=100_000_000)
    consent_to_contact: bool
    website: str | None = Field(default=None, max_length=200)

    @field_validator("company_name", "contact_name")
    @classmethod
    def clean_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("This field cannot be blank.")
        return cleaned

    @field_validator(
        "phone",
        "postcode",
        "change_timing",
        "current_supplier",
        "contract_expiry",
        "contract_type",
        "website",
        mode="before",
    )
    @classmethod
    def clean_optional_text(cls, value: Any):
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        cleaned = value.strip()
        return cleaned or None

    @field_validator("currency", mode="before")
    @classmethod
    def clean_currency(cls, value: Any):
        if value is None:
            return None
        if not isinstance(value, str):
            return value

        cleaned = value.strip().upper()
        if not cleaned:
            return None
        if len(cleaned) != 3 or not cleaned.isalpha():
            raise ValueError("Currency must be a 3-letter code.")
        return cleaned

    @field_validator("priorities")
    @classmethod
    def clean_priorities(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for priority in value:
            if not isinstance(priority, str):
                raise ValueError("Each priority must be text.")
            item = priority.strip()
            if not item:
                continue
            if len(item) > 80:
                raise ValueError("Each priority must be 80 characters or fewer.")
            if item not in cleaned:
                cleaned.append(item)
        return cleaned


class ReferralUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=50)
    notes: str | None = Field(default=None, max_length=5000)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def row_to_referral(row: Any) -> dict[str, Any]:
    item = dict(row)
    try:
        item["priorities"] = json.loads(item.get("priorities") or "[]")
    except (json.JSONDecodeError, TypeError):
        item["priorities"] = []

    item["consent_to_contact"] = bool(item.get("consent_to_contact"))
    return item


def save_referral(referral: ReferralRequest) -> int | None:
    # Honeypot submissions are accepted without being persisted.
    if referral.website:
        return None

    if not referral.consent_to_contact:
        raise ValueError(
            "You must agree to be contacted about your comparison request."
        )

    initialise_database()
    created_at = now_iso()

    statement = insert(referrals_table).values(
        company_name=referral.company_name,
        contact_name=referral.contact_name,
        email=str(referral.email),
        phone=referral.phone,
        postcode=referral.postcode,
        change_timing=referral.change_timing,
        priorities=json.dumps(referral.priorities),
        current_supplier=referral.current_supplier,
        current_annual_cost=referral.current_annual_cost,
        currency=referral.currency,
        contract_expiry=referral.contract_expiry,
        contract_type=referral.contract_type,
        monthly_mono_pages=referral.monthly_mono_pages,
        monthly_colour_pages=referral.monthly_colour_pages,
        consent_to_contact=referral.consent_to_contact,
        created_at=created_at,
        updated_at=created_at,
        status="new",
        notes=None,
    )

    with engine.begin() as connection:
        result = connection.execute(statement)
        referral_id = result.inserted_primary_key[0]

    if referral_id is None:
        raise RuntimeError("Referral was saved but no referral ID was returned.")
    return int(referral_id)


def get_referrals() -> list[dict[str, Any]]:
    initialise_database()
    statement = select(referrals_table).order_by(referrals_table.c.created_at.desc())

    with engine.connect() as connection:
        rows = connection.execute(statement).mappings().all()

    return [row_to_referral(row) for row in rows]


def get_referral(referral_id: int) -> dict[str, Any] | None:
    initialise_database()
    statement = select(referrals_table).where(referrals_table.c.id == referral_id)

    with engine.connect() as connection:
        row = connection.execute(statement).mappings().first()

    return None if row is None else row_to_referral(row)


def update_referral(referral_id: int, update: ReferralUpdate) -> dict[str, Any]:
    initialise_database()

    if update.status is not None and update.status not in REFERRAL_STATUSES:
        raise ValueError("Invalid referral status.")

    values: dict[str, Any] = {}
    if update.status is not None:
        values["status"] = update.status
    if update.notes is not None:
        values["notes"] = update.notes.strip()

    if not values:
        existing = get_referral(referral_id)
        if existing is None:
            raise KeyError("Referral not found.")
        return existing

    values["updated_at"] = now_iso()
    statement = (
        sql_update(referrals_table)
        .where(referrals_table.c.id == referral_id)
        .values(**values)
    )

    with engine.begin() as connection:
        result = connection.execute(statement)
        if result.rowcount == 0:
            raise KeyError("Referral not found.")

    updated = get_referral(referral_id)
    if updated is None:
        raise RuntimeError("Referral was updated but could not be reloaded.")
    return updated
