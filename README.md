# PrintSift

PrintSift is a full-stack contract-analysis application for copier and managed-print agreements. It extracts key commercial terms from uploaded PDF contracts, verifies the evidence behind extracted values, calculates estimated annual costs, and can capture comparison/referral requests for follow-up.

This repository is a **sanitised portfolio snapshot** of the project. The production repository remains private. Real customer/contract documents, databases, secrets, environment files and deployment-specific data are intentionally excluded.

## What it demonstrates

- Full-stack development with **Python / FastAPI** and **Next.js / TypeScript**
- Structured AI extraction with the **OpenAI API**
- PDF parsing, page selection and OCR detection
- Evidence tracing and verification against the source document
- Financial calculations from extracted contract terms
- REST API design and frontend/backend integration
- SQLAlchemy persistence with SQLite/PostgreSQL support
- Input validation with Pydantic
- Admin/referral workflow and CSV export
- Rate limiting, upload limits, CORS configuration and security headers
- Automated testing with pytest

## Core workflow

1. A user uploads a PDF contract.
2. The backend validates the file and extracts text with `pypdf`.
3. A relevance scorer selects the most commercially useful pages instead of sending the entire contract to the AI model.
4. The AI extractor returns typed contract data plus evidence quotes and page numbers.
5. PrintSift validates each evidence quote against the extracted source page.
6. The frontend displays the contract terms and lets the user calculate estimated annual costs from usage data.
7. Users can optionally submit a comparison request, which is stored for the admin workflow.

## Architecture

```text
frontend/                    Next.js / TypeScript UI
  src/app/                   Main application and admin pages
  src/components/            Reusable UI components
  src/lib/api.ts             API configuration

backend/
  app/main.py                FastAPI routes, security and request handling
  app/models.py              Typed contract/evidence models
  app/pdf.py                 PDF validation and text extraction
  app/relevance.py           Relevant-page scoring and selection
  app/extractors/ai.py       Structured AI extraction
  app/extractors/regex.py    Lightweight regex extraction fallback/benchmark
  app/validation.py          Evidence verification
  app/calculations.py        Contract cost calculations
  app/database.py            SQLAlchemy database configuration
  app/referrals.py           Referral data model and persistence
```

## Security / privacy choices

The public portfolio intentionally contains **no real contracts, referral records, database files or API keys**. The production application uses environment variables for secrets and database configuration. Uploads are size-limited, PDF metadata/content is validated, admin endpoints require a secret key, API routes are rate limited, CSV cells are protected against formula injection, and sensitive API responses are marked `no-store`.

This portfolio repository has fresh history and therefore does not inherit private production files that existed in the original repository history.

## Local setup

### Backend

```bash
cd backend
python -m venv .venv
# Activate the virtual environment
pip install -r requirements.txt
```

Create `backend/.env`:

```env
OPENAI_API_KEY=your_key_here
ADMIN_API_KEY=use_a_long_random_value_at_least_32_characters
DATABASE_URL=sqlite:///printsift.db
PRINTSIFT_ALLOWED_ORIGINS=http://localhost:3000
```

Run the API:

```bash
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Run the frontend:

```bash
npm run dev
```

## Testing

The private development project includes pytest coverage around the database layer, extraction fixtures and security hardening. Public tests in this snapshot avoid including real contract documents.

## Why I built it

I built PrintSift to explore a real commercial problem rather than only following tutorials. The project pushed me through document processing, typed APIs, data modelling, AI integration, testing, frontend state, database persistence, deployment and security decisions in one system.

## Portfolio note

This repository is intended to demonstrate engineering work. It is not a legal, financial or procurement service, and the extracted results should always be checked against the original contract.
