# Service Account Authentication for n8n → Cloud Run

## Problem Summary

Your GCP organization has a policy that prevents making Cloud Run services publicly accessible. The `allUsers` IAM binding failed with:

```
ERROR: FAILED_PRECONDITION: One or more users named in the policy do not belong to a permitted customer, perhaps due to an organization policy.
```

This means n8n cannot call the Cloud Run API without proper authentication.

## Solution: Service Account Authentication

Create a service account that n8n will use to authenticate with Cloud Run, then configure n8n to generate identity tokens for each API request.

---

## Step 1: Create Service Account in Cloud Shell

```bash
# Set project
gcloud config set project travel-rpa-pilot-473709

# Create service account
gcloud iam service-accounts create n8n-cloud-run-invoker \
  --display-name="n8n Cloud Run Invoker" \
  --description="Service account for n8n to invoke Cloud Run services"

# Grant Cloud Run Invoker role to the service account
gcloud run services add-iam-policy-binding travel-rpa-api \
  --region=us-central1 \
  --member="serviceAccount:n8n-cloud-run-invoker@travel-rpa-pilot-473709.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

# Create and download service account key
gcloud iam service-accounts keys create ~/n8n-sa-key.json \
  --iam-account=n8n-cloud-run-invoker@travel-rpa-pilot-473709.iam.gserviceaccount.com

# View the key file
cat ~/n8n-sa-key.json
```

**Important**: Copy the contents of `n8n-sa-key.json` - you'll need this in n8n.

---

## Step 2: Configure n8n Credentials

### Option A: Using Google Service Account Credential (Recommended)

1. **In n8n, go to Credentials → Add Credential**

2. **Select "Google Service Account"**

3. **Fill in the details from your `n8n-sa-key.json` file:**
   - Service Account Email: `n8n-cloud-run-invoker@travel-rpa-pilot-473709.iam.gserviceaccount.com`
   - Private Key: (paste the full private key from the JSON file, including `-----BEGIN PRIVATE KEY-----` and `-----END PRIVATE KEY-----`)

4. **Save the credential** with name: "Cloud Run Service Account"

### Option B: Using Google Cloud OAuth2 API (Alternative)

If Option A doesn't work, you can use OAuth2:

1. Go to GCP Console → APIs & Services → Credentials
2. Create OAuth 2.0 Client ID (Desktop application)
3. Download the credentials JSON
4. In n8n, create a "Google OAuth2 API" credential
5. Use the downloaded credentials

---

## Step 3: Update n8n Workflows to Use Authentication

### For WF-02 (Ingest Email)

**Current "Django API - Ingest" node needs updating:**

1. **Open WF-02 workflow in n8n**

2. **Find the "Django API - Ingest" HTTP Request node**

3. **Change Authentication settings:**
   - Authentication: **"Generic Credential Type"**
   - Generic Auth Type: **"Google Service Account"** (or the credential type you created)
   - Credential for Google Service Account: **Select "Cloud Run Service Account"**

4. **Update the URL (if needed):**
   - URL: `https://travel-rpa-api-965515975997.us-central1.run.app/api/v1/ingest`

5. **Keep the Headers section:**
   - Header Name: `X-Webhook-Secret`
   - Header Value: `{{ $env.N8N_WEBHOOK_SECRET }}`

6. **In the node's "Options" tab:**
   - Enable "Add Query Parameters"
   - Add parameter: `audience` = `https://travel-rpa-api-965515975997.us-central1.run.app`

The node will now automatically generate Google identity tokens for authentication.

### For WF-04 (Simulate Issuance)

**Update "Django API - Simulate Issuance" node the same way:**

1. Authentication: Google Service Account credential
2. Keep X-Webhook-Secret header
3. Add audience query parameter

---

## Step 4: Test the Authentication

### Test in Cloud Shell

```bash
# Get an identity token for the service account
TOKEN=$(gcloud auth print-identity-token \
  --impersonate-service-account=n8n-cloud-run-invoker@travel-rpa-pilot-473709.iam.gserviceaccount.com \
  --audiences=https://travel-rpa-api-965515975997.us-central1.run.app)

# Test the API with the token
curl -X POST https://travel-rpa-api-965515975997.us-central1.run.app/api/v1/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: 2oz3bYILS7DKUG03/kdG5OLuqBFcJuGF8NKaJzIagvI=" \
  -d '{
    "message_id": "test-123",
    "from": "test@example.com",
    "subject": "Test Travel Insurance",
    "body": "Hello, please issue an outbound travel policy.",
    "received_at": "2025-10-04T05:00:00Z",
    "thread_id": "thread-123",
    "ocr_results": []
  }'
```

**Expected response**: JSON with `{"route": "missing", ...}` or similar (NOT 403 Forbidden)

### Test in n8n

1. **In WF-02, click "Execute Workflow" (test mode)**

2. **Send a test webhook payload** or **trigger manually**

3. **Check the "Django API - Ingest" node output**
   - Should show JSON response
   - Should NOT show 403 error

---

## Alternative: Simpler HTTP Request Node Configuration

If the Google Service Account authentication is complex in n8n, you can use a Python script to generate tokens:

### Create Token Generator Script

```python
#!/usr/bin/env python3
import json
import google.auth
from google.auth.transport.requests import Request
from google.oauth2 import service_account

def get_identity_token(service_account_file, audience):
    credentials = service_account.IDTokenCredentials.from_service_account_file(
        service_account_file,
        target_audience=audience
    )
    credentials.refresh(Request())
    return credentials.token

if __name__ == "__main__":
    audience = "https://travel-rpa-api-965515975997.us-central1.run.app"
    token = get_identity_token("/path/to/n8n-sa-key.json", audience)
    print(token)
```

Then in n8n, use this token in the Authorization header: `Bearer {token}`

But note: tokens expire after 1 hour, so this approach requires token refresh logic.

---

## Troubleshooting

### Still getting 403 Forbidden

1. **Check service account has correct role:**
   ```bash
   gcloud run services get-iam-policy travel-rpa-api --region=us-central1
   ```
   
   Should show:
   ```yaml
   bindings:
   - members:
     - serviceAccount:n8n-cloud-run-invoker@travel-rpa-pilot-473709.iam.gserviceaccount.com
     role: roles/run.invoker
   ```

2. **Verify token is being sent:**
   - In n8n, check the HTTP Request node's raw request
   - Should have `Authorization: Bearer {long-token-string}`

3. **Check token audience:**
   - The audience parameter must match the Cloud Run service URL exactly

### n8n doesn't support Google Service Account authentication

If n8n's HTTP Request node doesn't have built-in Google authentication:

**Workaround**: Deploy a small Cloud Function that acts as a proxy:
1. Cloud Function accepts requests from n8n with X-Webhook-Secret
2. Cloud Function generates identity token internally
3. Cloud Function forwards to Cloud Run with proper auth
4. Returns response back to n8n

(This is more complex but avoids authentication issues in n8n)

---

## Security Notes

1. **Never commit `n8n-sa-key.json` to git**
   - It's already in `.gitignore` as `gcp-key.json` pattern
   - Keep it secure in n8n's credential manager only

2. **Principle of least privilege**
   - The service account only has `roles/run.invoker` permission
   - It cannot access other GCP resources

3. **Rotate keys periodically**
   - Create new service account keys every 90 days
   - Delete old keys after updating n8n

4. **Monitor usage**
   - Check Cloud Logging for unusual API calls
   - Set up alerts for failed authentication attempts

---

## Summary

The organization policy prevents public Cloud Run access, but service account authentication allows n8n to securely call the API. After completing these steps:

✅ Service account created with Cloud Run invoker permission  
✅ n8n configured with service account credentials  
✅ Workflows updated to use authenticated requests  
✅ Both `/api/v1/ingest` and `/api/v1/simulate-issuance` accessible from n8n  

Once authentication is working, proceed with the workflow updates in `/home/ubuntu/repos/Travel-RPA/n8n_workflows/UPDATE_GUIDE.md`.
