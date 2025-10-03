# Travel RPA Pilot - Email-based Policy Issuance Automation

Production-grade RPA + AI/NLP/OCR system for email-based travel policy issuance. Monitors email inbox, extracts policy requirements using regex and Google Vision OCR, calculates premiums using deterministic pricing rules, simulates policy issuance via Playwright, and responds with policy PDFs.

## Architecture

```
Gmail → n8n WF-01 (Ingest) → n8n WF-02 (Intent + OCR) → Django /api/v1/ingest →
Django (Pricing + Validation + DB) → Response to n8n →
n8n WF-03 (Missing Fields) OR n8n WF-04 (Success + Playwright + Email)
```

### Components

- **Orchestration**: n8n workflows for email triggers, routing, and notifications
- **Core Service**: Django REST API for business logic, pricing, validation, and database operations
- **OCR**: Google Vision API (via n8n) for passport data extraction
- **Pricing**: Deterministic engine using CSV tariffs + YAML rules (100% exact match SLO)
- **Database**: PostgreSQL with Case and Traveller models
- **Simulation**: Playwright for policy issuance simulation
- **Deployment**: GCP Cloud Run, Cloud SQL, Cloud Storage, Secret Manager

## Scope

- **In**: OUTBOUND travel policies (cases 6-25)
- **Out**: INBOUND policies (no tariff data provided)
- **Test Cases**: 20 outbound scenarios
- **SLOs**: Intent ≥98%, Extraction ≥99%, Pricing 100% exact, Latency p95 ≤60s

## Project Structure

```
travel_rpa/
├── manage.py
├── config/
│   ├── settings/
│   │   ├── base.py          # Base settings
│   │   ├── development.py   # Local development
│   │   └── production.py    # GCP Cloud Run
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── core/                # Case management, webhooks, models
│   │   ├── models.py        # Case and Traveller models
│   │   ├── views.py         # API endpoints
│   │   └── urls.py
│   ├── extraction/          # OCR processing, MRZ parser
│   │   └── mrz_parser.py    # Parse passport MRZ data
│   ├── pricing/             # Pricing engine
│   │   └── engine.py        # Deterministic premium calculation
│   └── issuance/            # Playwright simulation
│       └── simulator.py     # Simulate policy issuance
├── data/
│   ├── tariffs.csv          # Parsed from tariff PDF (40 entries)
│   └── rules.yml            # Pricing rules (age loads, sports, discounts)
└── tests/
    ├── test_pricing.py      # Unit tests for pricing engine
    ├── test_mrz_parser.py   # Unit tests for MRZ parser
    └── test_golden_set.py   # Integration tests (20 cases)
```

## Setup

### Prerequisites

- Python 3.12
- PostgreSQL (for production) or SQLite (for development)
- GCP account with project `travel-rpa-pilot-473709`

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run migrations
python travel_rpa/manage.py migrate

# Run development server
python travel_rpa/manage.py runserver
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```
DJANGO_SECRET_KEY=your-secret-key
N8N_WEBHOOK_SECRET=your-webhook-secret
DB_NAME=travel_rpa_pilot
DB_USER=rpauser
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
```

## API Endpoints

### POST /api/v1/ingest

Webhook endpoint called by n8n WF-02 after OCR.

**Request:**
```json
{
  "message_id": "string",
  "thread_id": "string",
  "from": "email@example.com",
  "subject": "string",
  "body": "string",
  "received_at": "2025-10-03T12:00:00Z",
  "ocr_results": ["OCR text 1", "OCR text 2"]
}
```

**Response (Success):**
```json
{
  "route": "success",
  "case_id": "uuid",
  "extracted": {
    "direction": "OUTBOUND",
    "scope": "WORLDWIDE",
    "plan": "Silver",
    "days": 10,
    "start_date": "2025-11-01",
    "end_date": "2025-11-10"
  },
  "pricing": {
    "base_per_traveller": "30.00",
    "subtotal": "30.00",
    "group_discount": "0.00",
    "net": "30.00",
    "tax": "0.00",
    "fees": "0.00",
    "total": "30.00",
    "currency": "USD"
  },
  "travellers": [
    {
      "name": "John Doe",
      "passport": "AB1234567",
      "age": 35,
      "is_senior": false
    }
  ]
}
```

**Response (Missing Fields):**
```json
{
  "route": "missing",
  "case_id": "uuid",
  "to": "requester@example.com",
  "missing": ["scope", "start_date"],
  "original_subject": "Travel Policy Request",
  "thread_id": "string"
}
```

### POST /api/v1/simulate-issuance

Playwright simulation endpoint called by n8n WF-04.

**Request:**
```json
{
  "case_id": "uuid"
}
```

**Response:**
```json
{
  "screenshot_url": "/tmp/issuance_screenshots/issuance_uuid.png",
  "policy_number": "TP-12345678",
  "simulation_timestamp": 1696339200.0
}
```

## Pricing Logic

Following automation report (lines 53-74):

1. `base_i = KB(scope, plan, band)` per traveller
2. `age_load_i = 0.75 * base_i` if senior (76-86) else 0
3. `sports_load_i = 0.50 * (base_i + age_load_i)` if sports else 0
4. `subtotal = Σ_i (base_i + age_load_i + sports_load_i)`
5. `group_disc = subtotal * tier_rate` (pre-tax)
6. `net = subtotal − group_disc`
7. `tax_amount = net * tax_rate`
8. `fees = issue_fee + payment_fee`
9. `gross = net + tax_amount + fees`
10. `final = max(round(gross, 2), min_premium)`

Group discounts: 5% (11-20), 15% (21-30), 25% (31-40), 35% (41+)

## Testing

```bash
# Run all tests
pytest travel_rpa/tests/ -v

# Run pricing engine tests
pytest travel_rpa/tests/test_pricing.py -v

# Run MRZ parser tests
pytest travel_rpa/tests/test_mrz_parser.py -v

# Run golden set integration tests
pytest travel_rpa/tests/test_golden_set.py -v
```

## Deployment

### Build Docker Image

```bash
cd /path/to/Travel-RPA
gcloud builds submit --tag gcr.io/travel-rpa-pilot-473709/travel-rpa-api
```

### Deploy to Cloud Run

```bash
gcloud run deploy travel-rpa-api \
  --image gcr.io/travel-rpa-pilot-473709/travel-rpa-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="DJANGO_SETTINGS_MODULE=config.settings.production" \
  --set-secrets="DATABASE_URL=DATABASE_URL:latest,N8N_WEBHOOK_SECRET=N8N_WEBHOOK_SECRET:latest" \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10
```

## n8n Workflow Integration

### Proposed Modifications (Requires User Approval)

#### WF-02 Classify + Validate

**Current**: JavaScript intent detection + Google Vision OCR + internal validation

**Proposed**:
- Keep Google Vision OCR node as-is
- Replace JavaScript validation nodes with HTTP Request node calling Django endpoint: `POST https://travel-rpa-api.run.app/api/v1/ingest`
- Pass: `message_id`, `thread_id`, `from`, `subject`, `body`, `received_at`, `ocr_results[]`
- Django returns: `{route: "success|missing|ignore", case_id, extracted_data, missing_fields[], pricing{}}`
- Use Switch node on `route` to trigger WF-03 or WF-04
- Add webhook secret in HTTP Request headers: `X-Webhook-Secret: ${N8N_WEBHOOK_SECRET}`

#### WF-04 Notify-Success

**Current**: Downloads static sample PDF from Google Drive

**Proposed**:
- Before downloading PDF, add HTTP Request node calling Django: `POST https://travel-rpa-api.run.app/api/v1/simulate-issuance`
- Pass: `case_id`
- Django runs Playwright simulation, returns: `{screenshot_url, policy_number, simulation_timestamp}`
- Include screenshot URL in success email body
- Keep existing Google Drive PDF download node for sample policy attachment

#### WF-01 Ingest and WF-03 Notify-Missing

No changes needed.

## Email Deliverability

Per workspace guide, configure:

1. Request Super Admin access for farah@limitless-tech.ai in Google Workspace Admin Console
2. Set up DKIM in Admin Console → Apps → Gmail → Authenticate email (2048-bit key)
3. Add DNS records at domain registrar:
   - SPF: `v=spf1 include:_spf.google.com ~all`
   - DKIM: Value from Admin Console
   - DMARC: `v=DMARC1; p=quarantine; pct=100; rua=mailto:dmarc@limitless-tech.ai; aspf=s; adkim=s`
4. Send seed test email to verify alignment before Oct 1 AM gate

## Known Limitations

1. **Tax Rates**: Set to 0% in rules.yml (need actual tax rate per scope/plan)
2. **Fees**: Issue fee and payment fee set to $0 (need actual fee amounts)
3. **Deductibles**: Found in general conditions PDF ($250 for seniors 76-86, $250 for sports) - documented but not applied to premiums
4. **Inbound Tariffs**: Not included (5 inbound test cases 1-5 excluded)
5. **Sample Policy PDF**: Static PDF from Google Drive (not dynamically generated)

## License

MIT

## Contact

- Devin Session: https://app.devin.ai/sessions/ea04391073bf4a4ebe0393b7544dfdef
- Requested by: @farahfarchoukh-ai
