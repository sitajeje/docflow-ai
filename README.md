# DocFlow AI

**AI-assisted invoice extraction, validation, and human review — built with Python, FastAPI, Docling, Gemini, PostgreSQL, Next.js, and n8n.**

> **Project status: local MVP / portfolio project.** The end-to-end document-processing and review flow has been exercised locally. This is **not** a production-ready accounting, payment, or French e-invoicing solution. See [Limitations and production-readiness roadmap](#limitations-and-production-readiness-roadmap).

## Overview

DocFlow AI helps operations and accounting teams reduce repetitive invoice data entry without handing financial decisions over to an LLM. Users upload a PDF invoice, extract text using Docling (with OCR for scanned documents), identify fields with either regex or Gemini, validate the results with deterministic Python rules, and review or correct them before approval.

The application separates **AI extraction**, **business validation**, **human decisions**, and **workflow notifications**. It also preserves an audit trail of review actions.

### Features

- **PDF intake:** upload PDF documents through a Next.js UI; parse them with Docling and OCR where needed.
- **Two extraction strategies:** regular expressions for known invoice templates and Gemini structured output for more variable layouts.
- **Typed validation:** Pydantic schemas, monetary normalization using Python `Decimal`, and amount-consistency checks.
- **Field-level review:** preserve extracted values and validation errors so reviewers can correct individual fields.
- **Persistent state:** PostgreSQL-backed review records, state transitions, and audit events via SQLAlchemy.
- **Human-in-the-loop:** review, correct, approve, or reject an invoice from the web interface.
- **Workflow automation:** n8n receives review notification events and can send email alerts.
- **Automated testing:** a Python pytest suite, plus manual end-to-end verification.

### Intended users

Small businesses, accounting firms, and administrative teams that manually process PDF invoices. The MVP is designed to demonstrate a practical solution architecture, **not** to replace professional accounting checks.

## Tech stack

| Layer | Technologies | Responsibility |
| --- | --- | --- |
| Frontend / BFF | Next.js, React, TypeScript, Tailwind CSS | Upload UI, review screens, server-side API proxy |
| Backend API | Python, FastAPI, Pydantic | API contracts, validation, business rules |
| Document parsing | Docling, OCR engine | PDF text and layout extraction |
| Information extraction | Regex, Google Gemini (`google-genai`) | Invoice field extraction |
| Persistence | PostgreSQL, SQLAlchemy 2.x, Psycopg | Review records and audit history |
| Automation | n8n, webhooks, email integration | Review notifications and orchestration |
| Quality | pytest, FastAPI TestClient | Unit and API tests |

## System architecture

```mermaid
flowchart TD
    U[User / reviewer] --> UI[Next.js UI and BFF]
    UI -->|PDF upload| API[FastAPI]
    API --> D[Docling / OCR]
    D --> M[Document Markdown]
    M --> E{Extraction strategy}
    E --> R[Regex]
    E --> G[Gemini structured output]
    R --> V[Pydantic + deterministic validation]
    G --> V
    V --> DB[(PostgreSQL: reviews + audit events)]
    UI <-->|Review / correct / approve / reject| API
    API <-->|State and audit events| DB
    API -->|Explicit notification request| N[n8n webhook]
    N --> MAIL[Email notification]
```

**Responsibility boundaries:**

- The **LLM proposes extracted values**; it does not authorize payments or directly update approval status.
- **FastAPI** owns business rules and review-state transitions.
- **PostgreSQL** persists data and related audit events.
- **n8n** orchestrates notifications. A successfully accepted webhook is **not** proof that an email was delivered.
- **Next.js** keeps backend API credentials on the server, but production deployment still requires actual user authentication and authorization.

## Project layout

The following summarizes the main files introduced across the six lessons (some optional files may differ in your local checkout):

```text
docflow-ai/
├── backend/
│   └── app/
│       ├── main.py
│       ├── api/
│       │   ├── invoices.py
│       │   ├── documents.py
│       │   └── reviews.py
│       ├── schemas/
│       │   ├── invoice.py
│       │   ├── document.py
│       │   ├── extraction.py
│       │   └── review.py
│       ├── services/
│       │   ├── invoice_validator.py
│       │   ├── document_parser.py
│       │   ├── regex_extractor.py
│       │   ├── llm_extractor.py
│       │   ├── extraction_validator.py
│       │   ├── invoice_extractor.py
│       │   └── review_validation.py
│       └── db/
│           ├── models.py
│           └── session.py
├── frontend/
│   ├── app/
│   │   ├── api/
│   │   ├── reviews/[id]/page.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── upload-form.tsx
│   │   └── review-editor.tsx
│   └── lib/
│       ├── api.ts
│       └── types.ts
├── scripts/
│   ├── init_db.py
│   └── test_ocr.py
├── tests/
│   ├── test_invoices.py
│   ├── test_documents.py
│   ├── test_extraction.py
│   └── test_reviews.py
├── workflows/                  # Exported n8n workflow JSON files
├── samples/                    # Public or synthetic examples only
├── requirements.txt
├── .env.example
└── README.md
```

## Local setup

### Prerequisites

- macOS, Linux, or Windows with a supported Python environment (developed locally with **Python 3.13**).
- Node.js and npm compatible with the installed Next.js and n8n versions.
- A reachable PostgreSQL database (e.g., a **separate Supabase project**).
- Gemini API key for the `llm` extraction method.
- n8n installed locally or running in Docker, if testing notifications.
- PDF/OCR dependencies supported by your operating system. Docling may download models on its first run.

### 1. Python backend

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate         # macOS / Linux
python -m pip install -r requirements.txt
```

On Windows, activate the environment with the appropriate PowerShell or Command Prompt activation script.

Create `.env` in the repository root (do **not** commit it):

```dotenv
GEMINI_API_KEY=replace_with_your_key
GEMINI_MODEL=gemini-2.5-flash
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/postgres?sslmode=require
DOCFLOW_API_KEY=replace_with_random_secret
DOCFLOW_REVIEWER_KEY=replace_with_another_random_secret
N8N_WEBHOOK_URL=http://localhost:5678/webhook-test/docflow-review
N8N_WEBHOOK_TOKEN=replace_with_webhook_secret
```

Create independent random secrets, for example:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

`DATABASE_URL` uses **PostgreSQL database credentials**, not Supabase `anon` or `service_role` API keys. URL-encode any special characters in passwords. The database must be reachable from your computer.

Initialize tables **for a fresh development database only**:

```bash
python -m scripts.init_db
```

Start FastAPI:

```bash
uvicorn backend.app.main:app --reload --port 8000
```

- API docs: <http://127.0.0.1:8000/docs>
- Health: <http://127.0.0.1:8000/health>

> `Base.metadata.create_all()` is a learning-stage initializer, not a migration tool. Use Alembic migrations before production deployment.

### 2. Next.js frontend

In another terminal:

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```dotenv
FASTAPI_URL=http://127.0.0.1:8000
DOCFLOW_API_KEY=replace_with_the_same_backend_api_key
DOCFLOW_REVIEWER_KEY=replace_with_the_same_backend_reviewer_key
```

Run the UI:

```bash
npm run dev
```

Open <http://localhost:3000>.

**Important:** the local BFF keeps keys out of browser bundles, but the lesson implementation does not yet authenticate individual users or enforce real reviewer roles. Keep this build **local/private only**.

### 3. n8n notification workflow

Start n8n using your existing local installation (for example `npx n8n`, or your established Docker Compose setup), and open <http://localhost:5678>.

1. Import the exported workflow from `workflows/` if available, or open the workflow **DocFlow AI - Invoice Review Notification** already created in n8n.
2. Configure its **Webhook** node for `POST /docflow-review` with Header Authentication: `X-Webhook-Token` equals `N8N_WEBHOOK_TOKEN`.
3. Add an **IF** node checking `{{$json.body.status}} == pending_review`.
4. Map `review_id` and create a `review_url` field: `{{ 'http://localhost:3000/reviews/' + $json.body.review_id }}`.
5. Configure the **Send Email** node with your own SMTP/email credentials and insert `review_url` in an HTML link.
6. In test mode, select **Listen for test event** and use the `webhook-test` URL. For an active/published workflow, switch to the production webhook URL.
7. Trigger **Notify reviewer** from a still-pending review, or call the FastAPI notification endpoint.

**Email link limitation:** `http://localhost:3000` works only on the computer running Next.js. Use an authenticated HTTPS deployment URL for remote reviewers.

**Notification behavior:** the current MVP triggers notifications explicitly; uploading an invoice does not automatically guarantee email delivery. A durable **Transactional Outbox** and dispatcher are planned production improvements.

If n8n runs inside Docker, `localhost` inside the container points to the container itself. Configure a reachable host/service address for any container-to-host callbacks.

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `POST` | `/invoices/validate` | Validate typed invoice data |
| `POST` | `/documents/parse` | Upload PDF and obtain Markdown |
| `POST` | `/invoices/extract` | Extract invoice fields from Markdown (`regex` or `llm`) |
| `POST` | `/review-items` | Extract and persist a review item |
| `GET` | `/review-items?limit=30` | List recent review items |
| `GET` | `/review-items/{id}` | Read review details |
| `GET` | `/review-items/{id}/source` | Retrieve stored source Markdown |
| `PATCH` | `/review-items/{id}/fields` | Correct permitted extracted fields |
| `POST` | `/review-items/{id}/approve` | Approve a validated review |
| `POST` | `/review-items/{id}/reject` | Reject a review with a reason |
| `GET` | `/review-items/{id}/events` | Read review audit history |
| `POST` | `/review-items/{id}/notify` | Request a notification through n8n |

For exact request/response schemas and headers, use the interactive FastAPI OpenAPI documentation at `/docs`.

### Example: structured extraction

```bash
curl -X POST http://127.0.0.1:8000/invoices/extract \
  -H 'Content-Type: application/json' \
  -d '{
    "method": "regex",
    "markdown": "FACTURE N° INV-2026-001\nFournisseur : Demo Consulting SAS\nDate : 27/10/2026\nTotal HT : 100,00 €\nTVA 20 % : 20,00 €\nTotal TTC : 120,00 €"
  }'
```

Example of a valid extraction response:

```json
{
  "status": "validated",
  "method": "regex",
  "invoice": {
    "vendor": "Demo Consulting SAS",
    "invoice_number": "INV-2026-001",
    "invoice_date": "2026-10-27",
    "subtotal": "100.00",
    "vat": "20.00",
    "total": "120.00",
    "currency": "EUR"
  },
  "errors": []
}
```

**Interpretation:** `validated` here means the extracted values passed the MVP's defined completeness and arithmetic checks — **not** that the invoice is authentic, tax-compliant, or authorized for payment.

## Typical review journey

1. Open the local Next.js workspace and upload an invoice PDF.
2. Choose regex (known template) or Gemini (variable format).
3. FastAPI parses PDF content, extracts fields, validates the result, and saves a `pending_review` record.
4. Open the review details. Compare extracted values against the source Markdown; correct identified errors only after checking the original invoice.
5. Save corrections and let the backend rerun deterministic validation.
6. Approve or reject the review (with business rules enforced by FastAPI).
7. Inspect the audit history.
8. Optionally click **Notify reviewer** to trigger the n8n email workflow.

Records use a hash of source Markdown plus extraction method to avoid identical repeated submissions in the local MVP. This is **not** sufficient business-level invoice deduplication across varying scans, vendors, or tenants.

## Testing and quality checks

From the repository root:

```bash
source .venv/bin/activate
python -m pytest -v
```

**Reported local milestone:** 27 Python tests passing at the end of Lesson 6. The suite covers invoice validation, PDF upload routes with mocked parsing, extraction and normalization, and persistent review API behavior. Actual Docling/OCR and Gemini integration must also be tested with real, non-sensitive sample documents; mocks alone cannot validate extraction accuracy.

Frontend checks:

```bash
cd frontend
npm run build
npm run lint     # if this script exists in your package.json
```

If no lint script is defined, use `npx eslint .`.

**Recommended additional tests before production:** PostgreSQL-specific concurrency/transaction tests, authentication and tenant-isolation tests, Playwright E2E coverage, failure/retry cases, and a labeled invoice extraction benchmark.

### Suggested benchmark metrics

- Field-level accuracy (invoice number, supplier, dates, subtotal, VAT, total)
- False acceptance / critical financial errors
- Average and p95 processing time
- Human review rate and correction time
- Cost per invoice, including AI/API, infrastructure, and labor
- Failure and retry rate by document type (digital PDF vs scan)

Do not advertise unmeasured accuracy, time savings, or cost reduction percentages.

## Limitations and production-readiness roadmap

This project is deliberately an **MVP**. Before handling real customer data or offering it as a public SaaS, implement and validate:

- [ ] **Authentication and authorization:** real user sessions, roles, reviewer identity derived from the session, and tenant-scoped access controls.
- [ ] **Secure originals:** private object storage for uploaded PDFs; authenticated access, retention, and deletion policies. The current review UI shows Markdown, not a secured original PDF viewer.
- [ ] **Async document jobs:** persistent queue, separate Docling/OCR workers, job IDs, cancellation/timeouts, and bounded retries. The local upload pipeline is synchronous.
- [ ] **Transactional Outbox:** atomically save review and notification event, then dispatch reliably to n8n with stable event IDs and idempotent consumers.
- [ ] **Concurrency-safe corrections:** row locks or optimistic version checks for edits as well as approvals.
- [ ] **Real invoice deduplication:** define business keys (e.g., tenant + supplier + invoice number), rather than relying solely on Markdown hashes.
- [ ] **Schema migrations:** Alembic-based migration history instead of using `create_all()` for evolving production schemas.
- [ ] **Security hardening:** rate limits, upload scanning, dependency updates, file-type verification, secrets management, logs that exclude sensitive data, and endpoint abuse protections.
- [ ] **Operational observability:** structured logs, metrics, error tracing, backups, restoration drills, and alerting.
- [ ] **Compliance review:** GDPR and relevant French accounting/e-invoicing obligations assessed with appropriate professional advice.
- [ ] **Extraction quality gate:** benchmark representative documents and capture human-verifiable evidence for critical fields.

The current email demo uses explicit notification triggering and local links; it should **not** be described as reliable, automated production notification delivery.

## Deployment direction

A plausible production-oriented separation is:

- **Next.js frontend/BFF:** managed hosting with authentication.
- **FastAPI API:** separately deployed container service.
- **Document workers:** independent containers with controlled CPU/memory and a persistent task queue.
- **PostgreSQL + object storage:** managed database and private document storage.
- **n8n:** managed or self-hosted integration orchestrator receiving controlled events.
- **CI/CD:** GitHub Actions for backend tests, frontend build, and deployment gates.

Deployment choices and exact operational costs should be validated for the intended customer and workload; this repository is not yet a push-button production deployment.

## Security and privacy

- Never commit `.env`, `frontend/.env.local`, database passwords, API keys, SMTP credentials, or private invoices.
- Use only public or synthetic files in the repository's `samples/` directory.
- Treat OCR text and external document content as untrusted input; never grant the LLM permission to approve invoices or make payments.
- Do not infer that passing arithmetic checks makes a document valid for accounting or tax purposes.
- Keep private customer information out of public screenshots, logs, test fixtures, and demo recordings.

## Portfolio and learning context

Developed as a six-part applied learning project:

1. FastAPI and n8n integration
2. Python modular architecture, Pydantic, and pytest
3. PDF parsing, Docling, OCR, and async architecture concepts
4. Gemini structured extraction and deterministic validation
5. PostgreSQL, persistent reviews, audit history, and n8n notifications
6. Next.js review workspace, BFF integration, testing, and deployment design

The goal is to demonstrate practical **AI product engineering**, combining Python backend development, document AI, workflow automation, frontend architecture, and business-oriented reliability design.

## License

No license is declared in this README. Add a `LICENSE` file only after choosing the intended licensing terms.
