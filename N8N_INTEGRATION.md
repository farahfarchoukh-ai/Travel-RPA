# Travel RPA - n8n Integration Guide

This guide explains how to integrate the Django REST API with your existing n8n workflows.

## Overview

The integration replaces client-side JavaScript data extraction with server-side Django processing, enabling:
- Centralized business logic in Django
- Database persistence for audit trails
- MRZ passport parsing via OCR
- Deterministic pricing engine
- Simulated policy issuance with Playwright

## Architecture

```
WF-01 (Email Monitor)
    ↓
WF-02 (Classify + Validate) → Django /api/v1/ingest
    ↓
WF-03 (Router) → Based on route (success/missing/ignore)
    ↓
WF-04 (Notify Success) → Django /api/v1/simulate-issuance
```

## Prerequisites

- Django API deployed to Cloud Run (see DEPLOYMENT.md)
- n8n workspace at https://farahfarchoukh.app.n8n.cloud
- API key with workflow edit permissions
- Same `N8N_WEBHOOK_SECRET` value configured in both n8n and Django

## Modified Workflows

### WF-02: Classify + Validate

**Changes:**
- **Removed:** JavaScript Code node (manual extraction)
- **Added:** HTTP Request node calling Django `/api/v1/ingest`

**Request Format:**
```json
POST https://YOUR-CLOUD-RUN-URL/api/v1/ingest
Headers:
  X-Webhook-Secret: ${N8N_WEBHOOK_SECRET}
  Content-Type: application/json

Body:
{
  "message_id": "{{ $json.id }}",
  "thread_id": "{{ $json.thread_id || $json.threadId }}",
  "from": "{{ $json.from }}",
  "subject": "{{ $json.subject }}",
  "body": "{{ $json.body || $json.snippet }}",
  "received_at": "{{ $json.received_at || $json.internalDate }}",
  "ocr_results": {{ $json.ocr_results || [] }}
}
```

**Response Format (Success Route):**
```json
{
  "route": "success",
  "case_id": "uuid-here",
  "extracted": {
    "direction": "OUTBOUND",
    "scope": "WORLDWIDE",
    "plan": "Silver",
    "days": 10,
    "start_date": "2025-11-01",
    "end_date": "2025-11-10",
    "sports_coverage": false
  },
  "travellers": [
    {
      "name": "JOHN DOE",
      "passport": "AB1234567",
      "age": 40,
      "is_senior": false
    }
  ],
  "pricing": {
    "base_per_traveller": "50.00",
    "subtotal": "50.00",
    "group_discount": "0.00",
    "net": "50.00",
    "tax": "0.00",
    "fees": "0.00",
    "total": "50.00",
    "currency": "USD"
  }
}
```

**Response Format (Missing Route):**
```json
{
  "route": "missing",
  "case_id": "uuid-here",
  "to": "customer@example.com",
  "missing": ["plan", "passport_numbers"],
  "original_subject": "Travel Insurance Request",
  "thread_id": "thread-id"
}
```

**Response Format (Ignore Route):**
```json
{
  "route": "ignore",
  "intent_ok": false
}
```

### WF-04: Notify Success

**Changes:**
- **Added:** HTTP Request node calling Django `/api/v1/simulate-issuance`
- **Modified:** Email HTML to include simulation screenshot link

**Request Format:**
```json
POST https://YOUR-CLOUD-RUN-URL/api/v1/simulate-issuance
Headers:
  X-Webhook-Secret: ${N8N_WEBHOOK_SECRET}
  Content-Type: application/json

Body:
{
  "case_id": "{{ $json.case_id }}"
}
```

**Response Format:**
```json
{
  "screenshot_url": "/path/to/screenshot.png",
  "policy_number": "POL-20251003-1234",
  "simulation_timestamp": "2025-10-03T12:00:00Z"
}
```

**Updated Email Template:**
```html
<p>Hello,</p>
<p>Your travel policy has been issued.</p>
<ul>
  <li>Scope: {{$('SE-Assemble').item.json.scope}}</li>
  <li>Plan: {{$('SE-Assemble').item.json.plan}}</li>
  <li>Dates: {{$('SE-Assemble').item.json.start_date}} ({{$('SE-Assemble').item.json.days}} days)</li>
  <li>Travellers: {{$('SE-Assemble').item.json.traveller_count}}</li>
  <li>Premium: {{$('SE-Assemble').item.json.currency}} {{$('SE-Assemble').item.json.premium_total}}</li>
</ul>
<p>Issuance simulation completed. <a href="{{$json.screenshot_url}}">View screenshot</a></p>
<p>Policy PDF attached.</p>
<p>— Insurance Operations</p>
```

## Step-by-Step Integration

### Step 1: Set Environment Variable in n8n

1. Go to n8n Settings → Variables
2. Add new environment variable:
   - **Name:** `N8N_WEBHOOK_SECRET`
   - **Value:** (same value as stored in GCP Secret Manager for Django)

### Step 2: Import Modified Workflows

#### Option A: Manual Import via UI

1. Download the modified workflow files:
   - `n8n_workflows/WF-02_modified.json`
   - `n8n_workflows/WF-04_modified.json`

2. In n8n, go to Workflows → Import from File

3. Select each JSON file and import

4. After importing, **CRITICAL:** Update the placeholder URL:
   - Find all nodes with `https://DJANGO_API_URL_HERE`
   - Replace with your actual Cloud Run URL: `https://travel-rpa-xxxxx-uc.a.run.app`

5. Save the workflows

6. Activate the workflows

#### Option B: Manual Modification of Existing Workflows

If you prefer to modify your existing workflows rather than importing new ones:

**For WF-02:**

1. Open WF-02 in n8n editor

2. Delete the "Code in JavaScript" node

3. Add a new "HTTP Request" node between Webhook and Switch:
   - **Method:** POST
   - **URL:** `https://YOUR-CLOUD-RUN-URL/api/v1/ingest`
   - **Authentication:** None (using custom header)
   - **Send Headers:** Yes
     - Add header: `X-Webhook-Secret` = `{{ $env.N8N_WEBHOOK_SECRET }}`
   - **Send Body:** Yes (JSON)
     - Body parameters:
       ```
       message_id: {{ $json.id || $json.message_id }}
       thread_id: {{ $json.thread_id || $json.threadId || $json.id }}
       from: {{ $json.from }}
       subject: {{ $json.subject }}
       body: {{ $json.body || $json.snippet || '' }}
       received_at: {{ $json.received_at || $json.internalDate || new Date().toISOString() }}
       ocr_results: {{ $json.ocr_results || [] }}
       ```

4. Connect nodes: Webhook → HTTP Request → Switch

5. The Switch node conditions remain unchanged (they check for `route` field)

6. Save and activate

**For WF-04:**

1. Open WF-04 in n8n editor

2. Add a new "HTTP Request" node after "SE-Assemble" and before "Download file":
   - **Method:** POST
   - **URL:** `https://YOUR-CLOUD-RUN-URL/api/v1/simulate-issuance`
   - **Authentication:** None (using custom header)
   - **Send Headers:** Yes
     - Add header: `X-Webhook-Secret` = `{{ $env.N8N_WEBHOOK_SECRET }}`
   - **Send Body:** Yes (JSON)
     - Body parameters:
       ```
       case_id: {{ $json.case_id }}
       ```

3. Add a new "Set" node after the HTTP Request node (before Download file):
   - **Assignments:**
     ```
     html: <p>Hello,</p>
           <p>Your travel policy has been issued.</p>
           <ul>
             <li>Scope: {{$('SE-Assemble').item.json.scope}}</li>
             <li>Plan: {{$('SE-Assemble').item.json.plan}}</li>
             <li>Dates: {{$('SE-Assemble').item.json.start_date}} ({{$('SE-Assemble').item.json.days}} days)</li>
             <li>Travellers: {{$('SE-Assemble').item.json.traveller_count}}</li>
             <li>Premium: {{$('SE-Assemble').item.json.currency}} {{$('SE-Assemble').item.json.premium_total}}</li>
           </ul>
           <p>Issuance simulation completed. <a href="{{$json.screenshot_url}}">View screenshot</a></p>
           <p>Policy PDF attached.</p>
           <p>— Insurance Operations</p>
     ```

4. Update the Gmail node to use `{{$('Assemble HTML').item.json.html}}` for the message body

5. Connect nodes: SE-Assemble → HTTP Request → Assemble HTML → Download file → Gmail → RW-200

6. Save and activate

### Step 3: Test the Integration

#### Test 1: Simple Success Case

Send a test email to your monitored inbox with:

**Subject:** Travel Insurance Request

**Body:**
```
Hello,

I need outbound travel insurance.

Details:
- Scope: Worldwide
- Plan: Silver
- Duration: 10 days
- Travel dates: 2025-11-01 to 2025-11-10
- Travellers: 1
- Name: John Doe
- Passport: AB1234567

Please process this request.
```

**Expected:**
1. WF-01 triggers and extracts email
2. WF-02 calls Django `/api/v1/ingest` successfully
3. Django returns `route: "success"` with pricing
4. WF-03 routes to WF-04
5. WF-04 calls Django `/api/v1/simulate-issuance`
6. Reply email sent with policy PDF and screenshot link

#### Test 2: Missing Data Case

Send a test email with missing plan:

**Subject:** Travel Insurance

**Body:**
```
Need insurance for worldwide trip, 5 days, starting 2025-12-01.
```

**Expected:**
1. Django returns `route: "missing"` with `missing: ["plan", "passport_numbers"]`
2. WF-03 routes to missing data handler
3. Reply email sent requesting missing information

#### Test 3: Ignore Case

Send an unrelated email:

**Subject:** Meeting Tomorrow

**Body:**
```
Hi, just confirming our meeting tomorrow at 3pm.
```

**Expected:**
1. Django returns `route: "ignore"` with `intent_ok: false`
2. WF-03 silently ignores (no reply sent)

### Step 4: Monitor and Debug

#### View n8n Execution Logs

1. Go to Executions tab in n8n
2. Click on recent execution
3. View each node's input/output
4. Check for errors in HTTP Request nodes

#### View Django Logs

```bash
# Stream Cloud Run logs
gcloud run services logs tail travel-rpa --region=us-central1

# Filter for errors
gcloud run services logs read travel-rpa \
  --region=us-central1 \
  --filter="severity>=ERROR" \
  --limit=50
```

#### Common Issues

**1. 401 Unauthorized Error**

**Symptom:** HTTP Request node returns 401
**Cause:** Webhook secret mismatch
**Fix:**
```bash
# Check Django secret
gcloud secrets versions access latest --secret="N8N_WEBHOOK_SECRET"

# Check n8n environment variable
# Settings → Variables → N8N_WEBHOOK_SECRET

# Ensure they match exactly
```

**2. Connection Timeout**

**Symptom:** HTTP Request node times out
**Cause:** Cloud Run cold start or long processing time
**Fix:**
- Increase n8n HTTP Request timeout to 60 seconds
- Increase Cloud Run timeout: `gcloud run services update travel-rpa --timeout=300 --region=us-central1`
- Consider setting min-instances=1 to avoid cold starts

**3. Invalid JSON Response**

**Symptom:** Switch node doesn't route correctly
**Cause:** Django returned error HTML instead of JSON
**Fix:**
- Check Django logs for exceptions
- Verify request payload format
- Test endpoint manually with curl

**4. Missing Fields in Response**

**Symptom:** Downstream nodes can't find expected fields
**Cause:** Django returned different structure than expected
**Fix:**
- Check Django response in n8n execution log
- Verify views.py response format matches expected schema
- Update Switch node conditions if needed

## Testing Checklist

- [ ] Environment variable `N8N_WEBHOOK_SECRET` set in n8n
- [ ] All placeholder URLs replaced with actual Cloud Run URL
- [ ] WF-02 HTTP Request node configured correctly
- [ ] WF-04 HTTP Request node configured correctly
- [ ] Email HTML template includes screenshot link
- [ ] Test email with complete data → success route
- [ ] Test email with missing data → missing route
- [ ] Test unrelated email → ignore route
- [ ] Reply emails sent successfully
- [ ] PDFs attached correctly
- [ ] Screenshot links work
- [ ] Pricing calculations correct
- [ ] Database records created in Django

## Performance Optimization

### Reduce Cold Start Latency

```bash
# Set minimum instances to avoid cold starts
gcloud run services update travel-rpa \
  --min-instances=1 \
  --region=us-central1
```

**Cost impact:** ~$5-10/month for keeping 1 instance warm

### Increase Concurrency

```bash
# Allow more concurrent requests per instance
gcloud run services update travel-rpa \
  --concurrency=80 \
  --region=us-central1
```

### Add Caching

Consider adding Redis for caching:
- Tariff data (rarely changes)
- Parsed MRZ data (for duplicate detection)
- Pricing calculations (for identical requests)

## Security Best Practices

1. **Webhook Secret Rotation:**
   ```bash
   # Generate new secret
   NEW_SECRET=$(openssl rand -base64 32)
   
   # Update in GCP
   echo -n "$NEW_SECRET" | gcloud secrets create N8N_WEBHOOK_SECRET_V2 --data-file=-
   
   # Update n8n environment variable
   # Update Django to use new secret
   # Test integration
   # Delete old secret
   ```

2. **IP Allowlisting (Optional):**
   - Get n8n egress IPs from n8n support
   - Configure Cloud Run to only accept requests from those IPs

3. **Rate Limiting:**
   - Configure Cloud Run to limit requests per IP
   - Add rate limiting middleware in Django

4. **Request Validation:**
   - Django already validates webhook secret
   - Add additional request validation (e.g., email format, date ranges)

## Rollback Procedure

If the integration causes issues:

1. **Quick Rollback:** Deactivate WF-02 and WF-04, activate old versions

2. **Partial Rollback:** Keep WF-02 integrated, rollback WF-04:
   - Remove HTTP Request node calling simulate-issuance
   - Restore old email template

3. **Full Rollback:** Restore original JavaScript extraction:
   - Replace HTTP Request node with original Code node
   - Restore original workflow structure

## Next Steps

After successful integration:

1. **Load Testing:** Test with 50+ concurrent emails
2. **Golden Set Testing:** Run all 20 test cases end-to-end
3. **Monitoring Setup:** Configure dashboards and alerts
4. **Documentation:** Document any custom modifications
5. **Training:** Train operators on HITL override process
6. **Go-Live:** Switch to production email inbox

## Support

For issues:
1. Check n8n execution logs first
2. Check Django Cloud Run logs
3. Test endpoints manually with curl
4. Review this guide for common issues
5. Contact support with:
   - n8n execution ID
   - Django log timestamps
   - Request/response payloads (redact PII)

## Appendix: API Endpoint Reference

### POST /api/v1/ingest

Processes incoming email and extracts policy data.

**Headers:**
- `X-Webhook-Secret`: Required. Must match Django's N8N_WEBHOOK_SECRET
- `Content-Type`: application/json

**Request Body:**
```json
{
  "message_id": "string (required)",
  "thread_id": "string (optional, defaults to message_id)",
  "from": "string (required)",
  "subject": "string (optional)",
  "body": "string (required)",
  "received_at": "ISO 8601 datetime (optional, defaults to now)",
  "ocr_results": ["MRZ string", "..."] (optional)
}
```

**Response (Success - 200):**
```json
{
  "route": "success|missing|ignore",
  "case_id": "uuid",
  "extracted": { /* policy data */ },
  "travellers": [{ /* traveller data */ }],
  "pricing": { /* pricing breakdown */ }
}
```

**Response (Error - 400):**
```json
{
  "error": "Error message",
  "route": "missing"
}
```

**Response (Unauthorized - 401):**
```json
{
  "error": "Unauthorized"
}
```

### POST /api/v1/simulate-issuance

Simulates policy issuance with Playwright.

**Headers:**
- `X-Webhook-Secret`: Required. Must match Django's N8N_WEBHOOK_SECRET
- `Content-Type`: application/json

**Request Body:**
```json
{
  "case_id": "uuid (required)"
}
```

**Response (Success - 200):**
```json
{
  "screenshot_url": "string",
  "policy_number": "string",
  "simulation_timestamp": "ISO 8601 datetime"
}
```

**Response (Not Found - 404):**
```json
{
  "error": "Case not found"
}
```

**Response (Unauthorized - 401):**
```json
{
  "error": "Unauthorized"
}
```
