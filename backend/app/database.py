import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import (
    Boolean,
    Column,
    Float,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
)
from sqlalchemy.engine import Engine

load_dotenv()

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parent.parent / "printsift.db"


def normalise_database_url(raw_url: str | None) -> str:
    if not raw_url:
        return "sqlite:///" + DEFAULT_DATABASE_PATH.as_posix()

    url = raw_url.strip()
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


DATABASE_URL = normalise_database_url(os.getenv("DATABASE_URL"))


def create_database_engine(database_url: str = DATABASE_URL) -> Engine:
    connect_args = {}
    if database_url.startswith("sqlite:"):
        connect_args["check_same_thread"] = False

    return create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


engine = create_database_engine()
metadata = MetaData()

referrals_table = Table(
    "referrals",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("company_name", String(200), nullable=False),
    Column("contact_name", String(200), nullable=False),
    Column("email", String(320), nullable=False),
    Column("phone", String(40)),
    Column("postcode", String(20)),
    Column("change_timing", String(50)),
    Column("priorities", Text, nullable=False, default="[]"),
    Column("current_supplier", String(200)),
    Column("current_annual_cost", Float),
    Column("currency", String(3)),
    Column("contract_expiry", String(100)),
    Column("contract_type", String(100)),
    Column("monthly_mono_pages", Integer),
    Column("monthly_colour_pages", Integer),
    Column("consent_to_contact", Boolean, nullable=False),
    Column("created_at", String(64), nullable=False),
    Column("updated_at", String(64)),
    Column("status", String(50), nullable=False, default="new"),
    Column("notes", Text),
)

Index("idx_referrals_created_at", referrals_table.c.created_at)
Index("idx_referrals_status", referrals_table.c.status)


def initialise_database(database_engine: Engine = engine):
    metadata.create_all(database_engine)
