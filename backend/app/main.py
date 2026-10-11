import csv
import io
import logging
import os
import secrets

from dotenv import load_dotenv

load_dotenv()

from fastapi import (
    Depends,
    FastAPI,
    File,
    Header,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.calculations import FinancialInputs, calculate_financials
from app.extractors.ai import analyse_contract_ai
from app.models import ContractData
from app.normalization import normalize_contract
from app.pdf import (
    PDFEncryptedError,
    PDFTextLimitError,
    PDFTooManyPagesError,
    PDFValidationError,
    extract_pdf_pages,
)
from app.referrals import (
    ReferralRequest,
    ReferralUpdate,
    get_referrals,
    save_referral,
    update_referral,
)
from app.relevance import format_selected_pages, select_relevant_pages
from app.validation import validate_evidence


logger = logging.getLogger("printsift.api")

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
UPLOAD_CHUNK_BYTES = 1024 * 1024
MAX_AI_TEXT_CHARACTERS = 300_000

ALLOWED_PDF_CONTENT_TYPES = {
    "application/pdf",
    "application/x-pdf",
    "application/octet-stream",
}


def get_allowed_origins() -> list[str]:
    configured = os.getenv("PRINTSIFT_ALLOWED_ORIGINS")
    if configured:
        return [
            origin.strip().rstrip("/")
            for origin in configured.split(",")
            if origin.strip()
        ]
    return ["http://localhost:3000", "http://127.0.0.1:3000"]


RATE_LIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=RATE_LIMIT_STORAGE_URI,
    headers_enabled=False,
)

app = FastAPI(title="PrintSift API", version="0.5.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "X-Admin-Key"],
)


class FinancialCalculationRequest(BaseModel):
    contract: ContractData
    usage: FinancialInputs


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"

    if request.url.path.startswith(
        ("/api/contracts", "/api/referrals", "/api/admin")
    ):
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"

    return response


def require_admin(x_admin_key: str | None = Header(default=None)):
    expected_key = os.getenv("ADMIN_API_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=500,
            detail="Admin access has not been configured.",
        )

    if len(expected_key) < 32:
        raise HTTPException(
            status_code=500,
            detail="Admin access has not been securely configured.",
        )

    if x_admin_key is None or not secrets.compare_digest(x_admin_key, expected_key):
        raise HTTPException(status_code=401, detail="Invalid admin key.")


async def read_upload_limited(file: UploadFile) -> bytes:
    contents = bytearray()

    try:
        while True:
            chunk = await file.read(UPLOAD_CHUNK_BYTES)
            if not chunk:
                break

            if len(contents) + len(chunk) > MAX_UPLOAD_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail="PDF must be smaller than 20 MB.",
                )

            contents.extend(chunk)
    finally:
        await file.close()

    if not contents:
        raise HTTPException(status_code=400, detail="The uploaded PDF is empty.")

    return bytes(contents)


def validate_upload_metadata(file: UploadFile):
    filename = (file.filename or "").strip()
    if not filename:
        raise HTTPException(status_code=400, detail="A PDF filename is required.")
    if len(filename) > 255:
        raise HTTPException(status_code=400, detail="The PDF filename is too long.")
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    content_type = (file.content_type or "").split(";", maxsplit=1)[0].strip().lower()
    if content_type and content_type not in ALLOWED_PDF_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")


def safe_csv_cell(value) -> str:
    if value is None:
        return ""

    text = str(value)
    candidate = text.lstrip()
    if candidate.startswith(("=", "+", "-", "@")) or text.startswith(
        ("\t", "\r", "\n")
    ):
        return "'" + text
    return text


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "PrintSift API"}


@app.post("/api/contracts/calculate")
@limiter.limit("60/minute")
def calculate_contract_cost(
    request: Request,
    payload: FinancialCalculationRequest,
):
    return calculate_financials(contract=payload.contract, inputs=payload.usage)


@app.post("/api/contracts/analyse")
@limiter.limit("6/minute")
async def analyse_uploaded_contract(
    request: Request,
    file: UploadFile = File(...),
):
    validate_upload_metadata(file)
    contents = await read_upload_limited(file)

    try:
        pages = extract_pdf_pages(contents)
        total_characters = sum(len(page.strip()) for page in pages)

        if total_characters < 500:
            return {
                "status": "ocr_required",
                "filename": file.filename,
                "page_count": len(pages),
                "message": (
                    "This PDF appears to be scanned or image-only. "
                    "OCR is required before PrintSift can analyse it."
                ),
            }

        selected = select_relevant_pages(pages, max_pages=25)
        selected_text = format_selected_pages(selected)

        if len(selected_text) > MAX_AI_TEXT_CHARACTERS:
            raise HTTPException(
                status_code=400,
                detail="This PDF contains too much text to analyse safely.",
            )

        result = analyse_contract_ai(selected_text)
        analysis = normalize_contract(result.data)
        validation = validate_evidence(pages, result.evidence)

        evidence = []
        for item, validation_result in zip(result.evidence, validation):
            evidence.append(
                {
                    **item.model_dump(),
                    "verified": validation_result["valid"],
                }
            )

        verified_count = sum(item["verified"] for item in evidence)

        return {
            "status": "complete",
            "filename": file.filename,
            "page_count": len(pages),
            "selected_pages": [page_number for page_number, _ in selected],
            "analysis": analysis.model_dump(),
            "evidence": evidence,
            "evidence_count": len(evidence),
            "verified_evidence_count": verified_count,
        }

    except HTTPException:
        raise
    except PDFEncryptedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PDFTooManyPagesError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PDFTextLimitError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PDFValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid readable PDF.",
        ) from exc
    except Exception as exc:
        logger.error("Contract analysis failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=500,
            detail="PrintSift could not analyse this contract. Please try again later.",
        ) from exc


@app.post("/api/referrals", status_code=201)
@limiter.limit("5/hour")
def create_referral(request: Request, referral: ReferralRequest):
    try:
        referral_id = save_referral(referral)
        return {
            "status": "received",
            "referral_id": referral_id,
            "message": "Your comparison request has been received.",
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/admin/referrals", include_in_schema=False)
@limiter.limit("60/minute")
def list_admin_referrals(
    request: Request,
    _admin: None = Depends(require_admin),
):
    referrals = get_referrals()
    return {"count": len(referrals), "referrals": referrals}


@app.patch("/api/admin/referrals/{referral_id}", include_in_schema=False)
@limiter.limit("60/minute")
def change_admin_referral(
    request: Request,
    referral_id: int,
    update: ReferralUpdate,
    _admin: None = Depends(require_admin),
):
    try:
        referral = update_referral(referral_id, update)
        return {"status": "updated", "referral": referral}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Referral not found.") from exc


@app.get("/api/admin/referrals/export.csv", include_in_schema=False)
@limiter.limit("10/minute")
def export_admin_referrals(
    request: Request,
    _admin: None = Depends(require_admin),
):
    referrals = get_referrals()
    output = io.StringIO(newline="")
    writer = csv.writer(output)

    writer.writerow(
        [
            "ID",
            "Status",
            "Company",
            "Contact",
            "Email",
            "Phone",
            "Postcode",
            "Change timing",
            "Priorities",
            "Current supplier",
            "Annual cost",
            "Currency",
            "Contract expiry",
            "Contract type",
            "Mono pages / month",
            "Colour pages / month",
            "Created",
            "Updated",
            "Notes",
        ]
    )

    for referral in referrals:
        row = [
            referral["id"],
            referral["status"],
            referral["company_name"],
            referral["contact_name"],
            referral["email"],
            referral["phone"],
            referral["postcode"],
            referral["change_timing"],
            ", ".join(referral["priorities"]),
            referral["current_supplier"],
            referral["current_annual_cost"],
            referral["currency"],
            referral["contract_expiry"],
            referral["contract_type"],
            referral["monthly_mono_pages"],
            referral["monthly_colour_pages"],
            referral["created_at"],
            referral["updated_at"],
            referral["notes"],
        ]
        writer.writerow([safe_csv_cell(value) for value in row])

    content = output.getvalue()
    output.close()

    return StreamingResponse(
        iter([content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="printsift-referrals.csv"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
