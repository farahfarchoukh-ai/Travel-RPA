# n8n Workflow Update Guide

## Overview

Your current WF-02 uses **JavaScript-based extraction** within n8n to parse emails and extract travel policy data. My modified WF-02 uses the **Django API** to handle all extraction, validation, and pricing logic.

## Key Differences

### Your Current WF-02 Approach:
1. **Code in JavaScript** node extracts data from email body using regex/parsing
2. **Get a message** (Gmail) fetches full email with attachments
3. **FX-ListAttachments** lists attachments
4. **Gmail Attachment (GET)** downloads each attachment
5. **Vision OCR** processes images with Google Cloud Vision API
6. **Code (Parse OCR)** extracts passport numbers and names from OCR results
7. **Switch** node routes based on extracted data completeness
8. **Notify-Missing** or **Notify-Success** HTTP requests to downstream workflows

### My Modified WF-02 Approach:
1. **Webhook** receives email notification
2. **Django API - Ingest** sends all data to Django (one HTTP request)
   - Django handles: intent detection, extraction, OCR, validation, pricing
   - Returns: route (missing/success/ignore), case_id, missing fields, extracted data
3. **Switch** node routes based on Django's response
4. **Respond to Webhook** returns status

## Why the Django Approach is Better

1. **Simpler n8n workflow**: 6 nodes vs 15+ nodes
2. **Centralized logic**: All business logic in Django (easier to test/maintain)
3. **Better error handling**: Django has comprehensive logging and validation
4. **Consistent data**: Single source of truth for extraction/pricing
5. **Easier testing**: Django has 35 golden test cases; n8n JavaScript is hard to test
6. **Performance**: Single API call vs multiple nodes and API calls

---

## BEFORE YOU START

**IMPORTANT**: Fix the 403 error first! The Django API must be working before you update the workflows.

Run this in Cloud Shell:
```bash
gcloud run services add-iam-policy-binding travel-rpa-api \
  --region=us-central1 \
  --member=allUsers \
  --role=roles/run.invoker
```

Test the API:
```bash
curl https://travel-rpa-api-965515975997.us-central1.run.app/api/v1/ingest \
  -H "X-Webhook-Secret: 2oz3bYILS7DKUG03/kdG5OLuqBFcJuGF8NKaJzIagvI=" \
  -d '{"message_id":"test"}'
```

You should see JSON response (not 403 HTML).

---

## Option A: Import My Modified Workflow (RECOMMENDED)

This is the easiest approach - replace your entire WF-02 with mine.

### Steps:

1. **Download the workflow file**
   - File: `/home/ubuntu/repos/Travel-RPA/n8n_workflows/WF-02_modified.json`
   - Download it to your local machine

2. **In n8n, go to your workflows page**
   - https://farahfarchoukh.app.n8n.cloud/workflows

3. **Import the workflow**
   - Click **"Import from File"** button (top right)
   - Select `WF-02_modified.json`
   - n8n will create a new workflow

4. **Configure the N8N_WEBHOOK_SECRET environment variable**
   - Go to Settings → Variables in n8n
   - Add variable: `N8N_WEBHOOK_SECRET` = `2oz3bYILS7DKUG03/kdG5OLuqBFcJuGF8NKaJzIagvI=`

5. **Activate the workflow**
   - Open the imported workflow
   - Click **"Active"** toggle (top right)

6. **Update WF-01 to call this workflow**
   - In WF-01, find the node that calls WF-02
   - Update the URL to point to the new workflow's webhook URL
   - Get webhook URL from: Webhook node → "Test URL" or "Production URL"

7. **Delete or deactivate your old WF-02**

---

## Option B: Manually Update Your Existing WF-02

If you prefer to keep your existing workflow and just modify it:

### Step 1: Add N8N_WEBHOOK_SECRET Environment Variable

1. Go to n8n Settings → Variables
2. Click **"Add Variable"**
3. Name: `N8N_WEBHOOK_SECRET`
4. Value: `2oz3bYILS7DKUG03/kdG5OLuqBFcJuGF8NKaJzIagvI=`
5. Save

### Step 2: Simplify the Workflow

1. **Keep these nodes:**
   - Webhook (entry point)
   - Switch (routing logic)
   - Respond to Webhook nodes (exits)

2. **Delete these nodes:**
   - "Code in JavaScript" (extraction logic)
   - "Get a message" (Gmail)
   - "FX-ListAttachments"
   - "If" (attachment check)
   - "Gmail Attachment (GET)"
   - "Vision OCR"
   - "Code (Parse OCR)"
   - All HTTP Request nodes (Notify-Missing, Notify-Success)

3. **Add new node: Django API - Ingest**
   - Type: HTTP Request
   - Method: POST
   - URL: `https://travel-rpa-api-965515975997.us-central1.run.app/api/v1/ingest`
   - Authentication: Generic Credential Type → HTTP Header Auth
   - Headers:
     - Name: `X-Webhook-Secret`
     - Value: `={{ $env.N8N_WEBHOOK_SECRET }}`
   - Body: Parameters
     ```
     message_id: {{ $json.id || $json.message_id }}
     thread_id: {{ $json.thread_id || $json.threadId || $json.id }}
     from: {{ $json.from }}
     subject: {{ $json.subject }}
     body: {{ $json.body || $json.snippet || '' }}
     received_at: {{ $json.received_at || $json.internalDate || new Date().toISOString() }}
     ocr_results: {{ $json.ocr_results || [] }}
     ```

### Step 3: Update Switch Node

Update the Switch node conditions to check Django's response:

1. **Route 1: Missing**
   - Condition: `{{ $json["route"] }}` equals `"missing"`
   - Output key: "Missing"

2. **Route 2: Success**
   - Condition: `{{ $json["route"] }}` equals `"success"`
   - Output key: "Success"

3. **Route 3: Ignore**
   - Condition: `{{ $json["route"] }}` equals `"ignore"`
   - Output key: "Ignore"

### Step 4: Update Response Nodes

Connect the Switch outputs to simplified response nodes:

1. **RW-Success** (connect to Switch → Success)
   - Type: Respond to Webhook
   - Response Body (JSON):
     ```json
     { "ok": true, "route": "success", "case_id": "{{$json.case_id}}" }
     ```

2. **RW-Missing** (connect to Switch → Missing)
   - Type: Respond to Webhook
   - Response Body (JSON):
     ```json
     { "ok": true, "route": "missing", "case_id": "{{$json.case_id}}", "missing": {{JSON.stringify($json.missing)}} }
     ```

3. **RW-Ignore** (connect to Switch → Ignore)
   - Type: Respond to Webhook
   - Response Body (JSON):
     ```json
     { "ok": true, "route": "ignore" }
     ```

### Step 5: Connect the Nodes

Flow: `Webhook → Django API - Ingest → Switch → [RW-Success / RW-Missing / RW-Ignore]`

### Step 6: Save and Activate

1. Save the workflow
2. Activate it (toggle in top right)
3. Test with a sample email

---

## WF-04 Updates (Email Composition with LLM)

Similarly, update WF-04 to use the Django API for policy simulation:

### Key Changes:

1. **Add Django API call**
   - Type: HTTP Request
   - Method: POST
   - URL: `https://travel-rpa-api-965515975997.us-central1.run.app/api/v1/simulate-issuance`
   - Headers: `X-Webhook-Secret: {{ $env.N8N_WEBHOOK_SECRET }}`
   - Body: `{"case_id": "{{ $json.case_id }}"}`

2. **Add LLM Email Composer node**
   - Type: OpenAI Chat Model
   - Model: GPT-4
   - System message: "You are a professional insurance operations assistant..."
   - User message: Pass all policy details from Django response

3. **Keep existing nodes**
   - Download file (Google Drive)
   - Send a message (Gmail)
   - Respond to Webhook

See `/home/ubuntu/repos/Travel-RPA/n8n_workflows/WF-04_modified.json` for the complete structure.

---

## Testing After Updates

### Test WF-02 (Classification & Validation)

Send a test email to `email.rpa@limitless-tech.ai`:

```
Subject: Travel Insurance Request

Hello, please issue an outbound travel policy for 1 traveller.
- Coverage: Worldwide Excluding US/Canada, Silver plan
- Dates: 2025-11-01 to 2025-11-10 (10 days)
- Traveler: John Smith, Passport AB1234567, DOB 1985-01-01
```

**Expected**: WF-02 classifies it as "success" and returns case_id

### Test WF-04 (Policy Issuance)

After WF-02 succeeds, WF-04 should:
1. Call Django API to simulate issuance
2. Use LLM to compose a professional email
3. Attach sample policy PDF
4. Send reply email

**Expected**: You receive a reply with LLM-generated content and PDF attachment

---

## Troubleshooting

### 403 Forbidden Error
- The IAM policy isn't set correctly
- Run the `gcloud run services add-iam-policy-binding` command above

### "X-Webhook-Secret" not defined
- Add `N8N_WEBHOOK_SECRET` to n8n Settings → Variables

### LLM node missing
- Install the "OpenAI" integration in n8n
- Add your OpenAI API key in Credentials

### Gmail/Google Drive credentials
- Add OAuth2 credentials in n8n for:
  - Gmail (`farah@limitless-tech.ai`)
  - Google Drive (for sample policy PDF)

### Django API returns 500 error
- Check Cloud Run logs:
  ```bash
  gcloud run logs read travel-rpa-api --region=us-central1 --limit=50
  ```

---

## Summary

**Recommendation**: Use Option A (import my modified workflows). It's faster and less error-prone.

**If using Option B**: Follow the manual steps carefully, especially the Switch node conditions and API authentication.

**After updates**: Test thoroughly with sample emails before going live.

**Support**: Review the complete setup guide at `/home/ubuntu/repos/Travel-RPA/FINAL_SETUP_GUIDE.md`
