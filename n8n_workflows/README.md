# n8n Workflow Integration Guide

This directory contains modified n8n workflow JSON files for the Travel RPA pilot automation system.

## Workflows

### WF-02: Classify + Validate (Modified for Django Integration)
**File:** `WF-02_modified.json`

**Purpose:** Ingests incoming emails, calls the Django API to extract and validate policy data, and routes based on the result.

**Flow:**
1. Webhook receives email data
2. Django API - Ingest: Calls `/api/v1/ingest` endpoint with email details
3. Switch: Routes based on response (`success`, `missing`, or `ignore`)
4. Respond with appropriate status

**Configuration Required:**
- Replace `https://DJANGO_API_URL_HERE` with your deployed Django API URL
- Set environment variable `N8N_WEBHOOK_SECRET` (must match Django's `N8N_WEBHOOK_SECRET`)
- Configure Gmail OAuth2 credentials

### WF-04: Notify-Success (with LLM Email Composition)
**File:** `WF-04_modified.json`

**Purpose:** Simulates policy issuance, generates a professional email using LLM, and sends the policy to the client.

**Flow:**
1. Webhook receives success notification
2. SE-Assemble: Prepares data
3. Django API - Simulate Issuance: Calls `/api/v1/simulate-issuance` to simulate frontend interaction
4. **LLM Email Composer**: Uses OpenAI/Claude to generate professional, context-aware email content
5. Extract HTML: Formats LLM output
6. Download file: Gets sample policy PDF from Google Drive
7. Send a message: Sends email with policy attachment via Gmail
8. RW-200: Returns success response

**LLM Integration:**
The LLM Email Composer node uses an AI language model to generate natural, professional email content based on:
- Policy details (direction, scope, plan, dates, travelers)
- Pricing breakdown
- Issuance screenshot URL
- Case ID

This provides:
- Natural, context-aware communication
- Personalized tone based on policy type (inbound/outbound, coverage level)
- Clear explanation of coverage and pricing
- Professional formatting

**Configuration Required:**
1. Replace `https://DJANGO_API_URL_HERE` with your deployed Django API URL
2. Set environment variable `N8N_WEBHOOK_SECRET`
3. Configure OpenAI API credentials:
   - Create an OpenAI account and get API key
   - Add credentials in n8n: Settings → Credentials → Add Credential → OpenAI
   - Update the `credentials` section in the LLM Email Composer node with your credential ID
4. Configure Gmail OAuth2 credentials
5. Configure Google Drive OAuth2 credentials
6. Update Google Drive file ID for the sample policy PDF

## Installation Instructions

### 1. Deploy Django API to GCP Cloud Run

Follow the deployment guide in `/DEPLOYMENT.md` to deploy the Django API. You'll receive a URL like:
```
https://travel-rpa-api-xxxxxx-uc.a.run.app
```

### 2. Import Workflows into n8n

1. Log in to your n8n workspace: https://farahfarchoukh.app.n8n.cloud
2. Click "Workflows" → "Add workflow" → "Import from File"
3. Import `WF-02_modified.json`
4. Import `WF-04_modified.json`

### 3. Configure Environment Variables

In n8n Settings → Variables, add:
```
N8N_WEBHOOK_SECRET=<same value as in Django deployment>
```

### 4. Update API URLs

In both workflows, find and replace:
```
https://DJANGO_API_URL_HERE
```
With your actual Cloud Run URL:
```
https://travel-rpa-api-xxxxxx-uc.a.run.app
```

### 5. Configure Credentials

Set up these credentials in n8n:

**Gmail OAuth2:**
1. Go to n8n Settings → Credentials → Add Credential
2. Select "Gmail OAuth2"
3. Follow the OAuth flow to connect `farah@limitless-tech.ai`

**Google Drive OAuth2:**
1. Add Credential → "Google Drive OAuth2"
2. Connect your Google account
3. Upload the sample policy PDF to Google Drive
4. Get the file ID from the URL and update in WF-04

**OpenAI API:**
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. In n8n: Add Credential → "OpenAI"
4. Paste your API key
5. Note the credential ID shown in n8n
6. Update WF-04's LLM Email Composer node with this credential ID

### 6. Test the Workflow

Send a test email to `email.rpa@limitless-tech.ai` with:
```
Subject: Travel Insurance Request

Body:
Hello, please issue an outbound travel policy for 1 traveller.
- Coverage: Worldwide Excluding US/Canada, Silver plan
- Dates: 2025-11-01 to 2025-11-10 (10 days)
- Traveler: John Smith, Passport AB1234567, DOB 1985-01-01

Thank you.
```

You should receive an automated response with:
- Professional, AI-generated email content
- Policy details and pricing
- Link to issuance screenshot
- Sample policy PDF attachment

## LLM Email Examples

### Success Case Output
```html
<p>Dear Valued Customer,</p>

<p>We're pleased to confirm that your travel insurance policy has been successfully issued!</p>

<h3>Policy Summary</h3>
<ul>
  <li><strong>Coverage:</strong> Outbound - Worldwide Excluding US/Canada</li>
  <li><strong>Plan:</strong> Silver ($50,000 coverage)</li>
  <li><strong>Travel Period:</strong> November 1-10, 2025 (10 days)</li>
  <li><strong>Travelers:</strong> JOHN SMITH</li>
  <li><strong>Total Premium:</strong> USD $30.00</li>
</ul>

<p>Your policy provides comprehensive coverage for medical emergencies, trip cancellations, 
and other travel-related incidents during your journey.</p>

<p>The complete policy document is attached to this email. We recommend reviewing it 
carefully and keeping a copy accessible during your travels.</p>

<p><a href="[screenshot_url]">View issuance confirmation →</a></p>

<p>Safe travels!</p>
<p>— Insurance Operations Team</p>
```

## Troubleshooting

**Issue: "Authentication failed"**
- Check that N8N_WEBHOOK_SECRET matches between n8n and Django
- Verify Gmail/Google Drive OAuth tokens haven't expired

**Issue: "OpenAI API error"**
- Verify your OpenAI API key is valid and has credits
- Check credential ID is correctly set in the workflow
- Review OpenAI usage limits

**Issue: "Django API timeout"**
- Check Cloud Run service is running
- Verify URL is correct (no trailing slash)
- Check Cloud Run logs for errors

**Issue: "LLM generates incorrect format"**
- Review the system prompt in the LLM Email Composer node
- Adjust the prompt to be more specific about HTML formatting
- Consider using a different model (GPT-4 vs GPT-3.5)

## Support

For issues with:
- n8n workflows: Contact n8n support or check https://docs.n8n.io
- Django API: Check Cloud Run logs with `gcloud run services logs read travel-rpa-api`
- LLM integration: Review OpenAI/Claude API documentation

## Architecture

```
Gmail Inbox
    ↓
[WF-01: Email Trigger] 
    ↓
[WF-02: Classify + Validate]
    ↓ (if success)
Django API (/api/v1/ingest)
    ↓
[WF-04: Notify Success]
    ↓
Django API (/api/v1/simulate-issuance)
    ↓
LLM (OpenAI/Claude) - Generate Email
    ↓
Gmail Send (with PDF attachment)
```

## Notes

- The sender email is `farah@limitless-tech.ai`
- The receiver/inbox email is `email.rpa@limitless-tech.ai`
- LLM usage incurs costs per API call (typically $0.01-0.10 per email depending on model)
- Consider using GPT-3.5-turbo for cost efficiency or GPT-4 for better quality
- The sample policy PDF should be uploaded to Google Drive and the file ID updated in WF-04
