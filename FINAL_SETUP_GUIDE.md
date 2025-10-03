# Travel RPA Pilot - Complete Setup Guide

This guide walks you through the entire setup process from start to finish.

## Overview

**What We're Building:**
An email automation system that monitors `email.rpa@limitless-tech.ai`, extracts travel policy data using AI/OCR, calculates premiums, and sends automated responses from `farah@limitless-tech.ai` with policy PDFs.

**Architecture:**
```
Gmail Inbox (email.rpa@limitless-tech.ai)
    ↓
n8n Workflow (Email Trigger + Classification)
    ↓
Django API on GCP Cloud Run (Data Extraction + Pricing)
    ↓
n8n Workflow (LLM Email Composition + Send via farah@limitless-tech.ai)
```

## Part 1: Fix GCP Permissions (YOU ARE HERE)

**What:** Grant storage access to Cloud Build service account  
**Why:** Cloud Build needs to read source code from Cloud Storage to build the Docker container  
**Time:** 2-3 minutes

### Steps:

1. **Open GCP IAM Console**
   - Go to: https://console.cloud.google.com/iam-admin/iam?project=travel-rpa-pilot-473709
   - You'll see a list of service accounts with their roles

2. **Find the Compute Engine Service Account**
   - Look for: `965515975997-compute@developer.gserviceaccount.com`
   - It should say "Compute Engine default service account"

3. **Add Storage Access Role**
   - Click the pencil icon ✏️ on the right side of that row
   - In the panel that opens, click "+ ADD ANOTHER ROLE"
   - In the "Select a role" dropdown, type: `Storage Object Viewer`
   - Select it from the results
   - Click "SAVE" at the bottom

4. **Verify**
   - The service account should now have multiple roles including "Storage Object Viewer"

**If the service account doesn't exist:**
   - Click "+ GRANT ACCESS" at the top
   - New principals: `965515975997-compute@developer.gserviceaccount.com`
   - Role: Search for "Storage Object Viewer"
   - Click "SAVE"

**✅ Once complete, tell Devin: "Permissions fixed, please deploy"**

---

## Part 2: Deploy Django API to GCP Cloud Run (DEVIN DOES THIS)

**What:** Deploy the Django REST API to Google Cloud  
**Why:** n8n needs a hosted API to process emails  
**Time:** 5-10 minutes

Devin will run:
```bash
gcloud run deploy travel-rpa-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="..." \
  --memory=1Gi
```

**Expected Result:**
- Service deployed to: `https://travel-rpa-api-XXXXX-uc.a.run.app`
- This URL will be used in n8n workflows

---

## Part 3: Import n8n Workflows (YOU DO THIS)

**What:** Import modified workflow JSON files into your n8n workspace  
**Why:** Connect email triggers to the deployed Django API  
**Time:** 10 minutes

### Files to Import:
- `n8n_workflows/WF-02_modified.json` - Email classification & validation
- `n8n_workflows/WF-04_modified.json` - Success notification with LLM email composition

### Steps:

1. **Download Workflow Files from GitHub**
   - Go to: https://github.com/farahfarchoukh-ai/Travel-RPA/tree/main/n8n_workflows
   - Download both modified JSON files to your computer

2. **Import WF-02 (Classification)**
   - Log in to: https://farahfarchoukh.app.n8n.cloud
   - Click "Workflows" in the left sidebar
   - Click "Add workflow" → "Import from File"
   - Select `WF-02_modified.json`
   - Click "Import"

3. **Import WF-04 (Success Notification)**
   - Repeat the same process for `WF-04_modified.json`

---

## Part 4: Configure n8n Workflows (YOU DO THIS)

**What:** Update workflows with your deployed API URL and credentials  
**Why:** Workflows need to know where to send data  
**Time:** 15 minutes

### A. Update API URLs in Both Workflows

1. **In WF-02 (Classification):**
   - Find the node: "Django API - Ingest"
   - Click on it
   - Find the URL field: `https://DJANGO_API_URL_HERE/api/v1/ingest`
   - Replace with: `https://travel-rpa-api-XXXXX-uc.a.run.app/api/v1/ingest`
   - (Use the actual URL from Part 2)

2. **In WF-04 (Success Notification):**
   - Find the node: "Django API - Simulate Issuance"
   - Click on it
   - Find the URL field: `https://DJANGO_API_URL_HERE/api/v1/simulate-issuance`
   - Replace with: `https://travel-rpa-api-XXXXX-uc.a.run.app/api/v1/simulate-issuance`

### B. Set Environment Variable

1. Go to n8n Settings → Variables
2. Add new variable:
   - Name: `N8N_WEBHOOK_SECRET`
   - Value: (Use the same secret that was set during Django deployment - Devin will provide this)

### C. Configure OpenAI Credentials for LLM

1. **Get OpenAI API Key:**
   - Go to: https://platform.openai.com/api-keys
   - Click "Create new secret key"
   - Copy the key (starts with `sk-`)

2. **Add to n8n:**
   - Go to n8n Settings → Credentials
   - Click "Add Credential"
   - Select "OpenAI"
   - Paste your API key
   - Save
   - **Note the Credential ID** (you'll see it in the URL or credential list)

3. **Update WF-04 Workflow:**
   - Open WF-04 workflow
   - Find the node: "LLM Email Composer"
   - Click on it
   - Under "Credentials" section
   - Replace `YOUR_OPENAI_CREDENTIALS_ID` with the actual ID from step 2
   - Save the workflow

### D. Configure Gmail OAuth2

1. **For Sending (in WF-04):**
   - Find the node: "Send a message1"
   - Click on "Credentials" dropdown
   - Select "Create New Credential"
   - Choose "Gmail OAuth2"
   - Follow OAuth flow to connect `farah@limitless-tech.ai`
   - Authorize the connection

2. **For Receiving (in WF-01 - if you have it):**
   - Similar process for the Gmail Trigger node
   - Connect `email.rpa@limitless-tech.ai`

### E. Configure Google Drive (for Policy PDF)

1. **Upload Sample Policy:**
   - Go to: https://drive.google.com
   - Upload the file: `Demo Travel Insurance Policy.docx.pdf`
   - Right-click → "Get link" → Copy the File ID from the URL
   - File ID looks like: `1a2b3c4d5e6f7g8h9i0j`

2. **Update WF-04:**
   - Find the node: "Download file"
   - Click on it
   - Update the "File ID" field with your File ID
   - Configure Google Drive OAuth2 credentials (similar to Gmail)

---

## Part 5: Test the System (YOU DO THIS)

**What:** Send test emails to verify end-to-end automation  
**Why:** Ensure everything works before going live  
**Time:** 15 minutes

### Test Case 1: Simple Outbound Policy

**Send email to:** `email.rpa@limitless-tech.ai`

**Subject:** Travel Insurance Request

**Body:**
```
Hello,

Please issue an outbound travel policy:
- Coverage: Worldwide Excluding US/Canada, Silver plan
- Dates: November 1-10, 2025 (10 days)
- Traveler: John Smith
- Passport: AB1234567
- Date of Birth: 1985-01-01

Thank you.
```

**Expected Result:**
- Within 2-3 minutes, receive automated email from `farah@limitless-tech.ai`
- Email contains professional LLM-generated content
- Policy details and pricing included
- Sample policy PDF attached

### Test Case 2: Inbound Policy

**Send email to:** `email.rpa@limitless-tech.ai`

**Subject:** Inbound Insurance - Silver Coverage

**Body:**
```
Hi,

My client is visiting Beirut. Please issue inbound policy:
- Coverage: Silver plan (10 days)
- Dates: November 15-24, 2025
- Traveler: Mary Johnson
- Passport: CD9876543
- DOB: 1990-05-15

Regards.
```

**Expected Result:**
- Automated response with inbound pricing ($45 for 10 days Silver)
- Professional email from LLM
- Policy PDF attached

### Test Case 3: Missing Data (Should Request Info)

**Send email to:** `email.rpa@limitless-tech.ai`

**Subject:** Policy Request

**Body:**
```
Please issue a travel policy for next month. Thanks.
```

**Expected Result:**
- Automated response asking for missing information
- Should list required fields: direction, coverage scope, dates, traveler details, etc.

---

## Part 6: Monitor & Debug (IF ISSUES OCCUR)

### Check n8n Workflow Executions

1. Go to: https://farahfarchoukh.app.n8n.cloud/executions
2. Click on the most recent execution
3. View each node's input/output
4. Look for red error indicators

### Check GCP Cloud Run Logs

**In Terminal:**
```bash
gcloud auth activate-service-account --key-file=gcp-key.json
gcloud config set project travel-rpa-pilot-473709
gcloud run services logs read travel-rpa-api --region=us-central1 --limit=50
```

**In GCP Console:**
1. Go to: https://console.cloud.google.com/run?project=travel-rpa-pilot-473709
2. Click on "travel-rpa-api"
3. Click "LOGS" tab
4. View recent requests and errors

### Common Issues & Solutions

**Issue:** "Authentication failed" in n8n
- **Solution:** Check N8N_WEBHOOK_SECRET matches between n8n and Django

**Issue:** "OpenAI API error" in LLM node
- **Solution:** Verify API key is valid and has credits; check credential ID is correct

**Issue:** "Connection timeout" to Django API
- **Solution:** Verify Cloud Run service is running; check URL has no trailing slash

**Issue:** "Missing required fields" for all emails
- **Solution:** Check extraction regex patterns in `views.py`; may need adjustment

**Issue:** "Pricing error" for valid policies
- **Solution:** Check `tariffs.csv` has correct rates; verify day band logic

---

## Part 7: Production Checklist (BEFORE LIVE USE)

- [ ] All test cases pass (outbound, inbound, missing data)
- [ ] Tariff rates verified against official documents
- [ ] Email templates approved by stakeholders
- [ ] LLM prompts reviewed and tested for professionalism
- [ ] Cost monitoring set up (OpenAI, GCP Cloud Run)
- [ ] Error alerting configured
- [ ] Backup/recovery plan documented
- [ ] Access controls reviewed (who can modify workflows)
- [ ] Data retention policy defined
- [ ] Compliance review complete (PDPA/DPIA if required)

---

## Quick Reference

### Important URLs
- **n8n Workspace:** https://farahfarchoukh.app.n8n.cloud
- **GCP Console:** https://console.cloud.google.com/run?project=travel-rpa-pilot-473709
- **GitHub Repo:** https://github.com/farahfarchoukh-ai/Travel-RPA
- **OpenAI Dashboard:** https://platform.openai.com/account/usage

### Email Addresses
- **Sender:** farah@limitless-tech.ai
- **Receiver/Inbox:** email.rpa@limitless-tech.ai

### Key Files
- Tariffs: `travel_rpa/data/tariffs.csv`
- Rules: `travel_rpa/data/rules.yml`
- Modified Workflows: `n8n_workflows/WF-02_modified.json`, `WF-04_modified.json`
- Deployment Guide: `DEPLOYMENT.md`
- Integration Guide: `N8N_INTEGRATION.md`

### Estimated Costs (Monthly)
- **GCP Cloud Run:** $5-15 (based on 100-500 requests/month)
- **OpenAI API:** $10-25 (GPT-3.5: ~$0.10/email, GPT-4: ~$0.30/email)
- **n8n Cloud:** Variable based on your plan
- **Total:** ~$15-40/month for pilot volume

---

## Support Contacts

**For Technical Issues:**
- GCP Support: Use GCP Console support chat
- n8n Support: https://docs.n8n.io or community forum
- OpenAI Support: https://help.openai.com

**For Business Logic:**
- Review tariffs in: `travel_rpa/data/tariffs.csv`
- Review pricing rules in: `travel_rpa/data/rules.yml`
- Check golden test cases in: `travel_rpa/tests/golden/`

---

## Next Steps After Setup

1. **Gradual Rollout:** Start with manual testing, then limited production
2. **Monitor Metrics:** Track response times, pricing accuracy, email delivery
3. **Gather Feedback:** Review LLM-generated emails for quality
4. **Iterate:** Adjust prompts, rules, and tariffs as needed
5. **Scale:** Once stable, increase volume and add features

---

**Last Updated:** October 3, 2025  
**Devin Session:** https://app.devin.ai/sessions/ea04391073bf4a4ebe0393b7544dfdef  
**PR:** https://github.com/farahfarchoukh-ai/Travel-RPA/pull/2
