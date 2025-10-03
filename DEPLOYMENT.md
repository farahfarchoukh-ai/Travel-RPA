# Travel RPA Pilot - Deployment Guide

This guide walks through deploying the Django REST API to Google Cloud Platform (GCP) Cloud Run.

## Prerequisites

- GCP Project ID: `travel-rpa-pilot-473709`
- Service account with appropriate permissions (provided by user)
- Docker installed locally for testing
- gcloud CLI installed and authenticated

## Architecture Overview

```
n8n Workflows → Django REST API (Cloud Run) → PostgreSQL (Cloud SQL)
                      ↓
              Cloud Storage (emails, PDFs, screenshots)
                      ↓
              Playwright Simulator
```

## Step 1: Set Up GCP Resources

### 1.1 Enable Required APIs

```bash
gcloud config set project travel-rpa-pilot-473709

gcloud services enable \
  run.googleapis.com \
  sql-component.googleapis.com \
  sqladmin.googleapis.com \
  storage-api.googleapis.com \
  secretmanager.googleapis.com
```

### 1.2 Create Cloud SQL PostgreSQL Instance

```bash
gcloud sql instances create travel-rpa-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --root-password=CHANGE_ME_STRONG_PASSWORD

# Create database
gcloud sql databases create travel_rpa --instance=travel-rpa-db

# Create user
gcloud sql users create travel_rpa_user \
  --instance=travel-rpa-db \
  --password=CHANGE_ME_STRONG_PASSWORD
```

### 1.3 Create Cloud Storage Buckets

```bash
# For storing raw emails, OCR results, PDFs
gsutil mb -p travel-rpa-pilot-473709 -l us-central1 gs://travel-rpa-storage

# Set lifecycle rules (optional - delete old files)
cat > lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 14, "matchesPrefix": ["passports/"]}
      },
      {
        "action": {"type": "Delete"},
        "condition": {"age": 180, "matchesPrefix": ["audits/"]}
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://travel-rpa-storage
```

### 1.4 Store Secrets in Secret Manager

```bash
# Database URL
echo -n "postgresql://travel_rpa_user:CHANGE_ME_STRONG_PASSWORD@/travel_rpa?host=/cloudsql/travel-rpa-pilot-473709:us-central1:travel-rpa-db" | \
  gcloud secrets create DATABASE_URL --data-file=-

# Django Secret Key (generate strong random key)
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" | \
  gcloud secrets create DJANGO_SECRET_KEY --data-file=-

# n8n Webhook Secret (use same value as in n8n)
echo -n "YOUR_N8N_WEBHOOK_SECRET_HERE" | \
  gcloud secrets create N8N_WEBHOOK_SECRET --data-file=-

# Grant Cloud Run service account access to secrets
gcloud secrets add-iam-policy-binding DATABASE_URL \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding DJANGO_SECRET_KEY \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding N8N_WEBHOOK_SECRET \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Step 2: Build and Deploy Django Application

### 2.1 Build Docker Image

```bash
cd travel_rpa

# Build image
docker build -t gcr.io/travel-rpa-pilot-473709/travel-rpa:latest .

# Test locally (optional)
docker run -p 8000:8000 \
  -e DATABASE_URL="sqlite:///db.sqlite3" \
  -e DJANGO_SECRET_KEY="test-secret" \
  -e N8N_WEBHOOK_SECRET="test-secret" \
  gcr.io/travel-rpa-pilot-473709/travel-rpa:latest

# Push to Google Container Registry
docker push gcr.io/travel-rpa-pilot-473709/travel-rpa:latest
```

### 2.2 Deploy to Cloud Run

```bash
gcloud run deploy travel-rpa \
  --image=gcr.io/travel-rpa-pilot-473709/travel-rpa:latest \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --min-instances=0 \
  --max-instances=10 \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300 \
  --set-env-vars="DJANGO_SETTINGS_MODULE=config.settings.production" \
  --set-secrets="DATABASE_URL=DATABASE_URL:latest,DJANGO_SECRET_KEY=DJANGO_SECRET_KEY:latest,N8N_WEBHOOK_SECRET=N8N_WEBHOOK_SECRET:latest" \
  --add-cloudsql-instances=travel-rpa-pilot-473709:us-central1:travel-rpa-db

# Note the URL returned (e.g., https://travel-rpa-xxxxx-uc.a.run.app)
```

### 2.3 Run Database Migrations

```bash
# Option 1: Use Cloud Run Jobs (recommended)
gcloud run jobs create travel-rpa-migrate \
  --image=gcr.io/travel-rpa-pilot-473709/travel-rpa:latest \
  --region=us-central1 \
  --set-env-vars="DJANGO_SETTINGS_MODULE=config.settings.production" \
  --set-secrets="DATABASE_URL=DATABASE_URL:latest,DJANGO_SECRET_KEY=DJANGO_SECRET_KEY:latest" \
  --add-cloudsql-instances=travel-rpa-pilot-473709:us-central1:travel-rpa-db \
  --command="python,manage.py,migrate"

gcloud run jobs execute travel-rpa-migrate --region=us-central1

# Option 2: Use Cloud SQL Proxy locally
cloud_sql_proxy -instances=travel-rpa-pilot-473709:us-central1:travel-rpa-db=tcp:5432 &
export DATABASE_URL="postgresql://travel_rpa_user:PASSWORD@localhost:5432/travel_rpa"
python manage.py migrate
```

## Step 3: Configure n8n Workflows

Now update your n8n workflows with the deployed Cloud Run URL.

### 3.1 Get Cloud Run URL

```bash
gcloud run services describe travel-rpa --region=us-central1 --format="value(status.url)"
# Output: https://travel-rpa-xxxxx-uc.a.run.app
```

### 3.2 Update n8n Workflows

1. Import the modified workflow JSON files:
   - `n8n_workflows/WF-02_modified.json`
   - `n8n_workflows/WF-04_modified.json`

2. In each workflow, replace `https://DJANGO_API_URL_HERE` with your actual Cloud Run URL:
   - WF-02: `https://travel-rpa-xxxxx-uc.a.run.app/api/v1/ingest`
   - WF-04: `https://travel-rpa-xxxxx-uc.a.run.app/api/v1/simulate-issuance`

3. Set the environment variable in n8n:
   - `N8N_WEBHOOK_SECRET` = same value as stored in GCP Secret Manager

### 3.3 Test the Integration

Send a test email to trigger WF-01, which should:
1. Extract email content and call WF-02
2. WF-02 calls Django `/api/v1/ingest` endpoint
3. Django returns route (success/missing/ignore)
4. If success, WF-03 calls WF-04
5. WF-04 calls Django `/api/v1/simulate-issuance` endpoint
6. WF-04 sends reply email with PDF

## Step 4: Monitoring and Observability

### 4.1 View Cloud Run Logs

```bash
# Stream logs
gcloud run services logs tail travel-rpa --region=us-central1

# View specific logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=travel-rpa" \
  --limit=50 \
  --format=json
```

### 4.2 Set Up Alerts (Optional)

```bash
# Create alert for error rate
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Travel RPA Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05 \
  --condition-threshold-duration=300s \
  --condition-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="travel-rpa" AND severity="ERROR"'
```

### 4.3 Monitor Database

```bash
# View database metrics
gcloud sql operations list --instance=travel-rpa-db

# Connect to database
gcloud sql connect travel-rpa-db --user=travel_rpa_user --database=travel_rpa
```

## Step 5: Cost Management

### 5.1 Set Budget Alerts

```bash
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="Travel RPA Monthly Budget" \
  --budget-amount=100USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

### 5.2 Estimated Costs (USD/month)

- Cloud Run: $5-20 (depends on usage)
- Cloud SQL (db-f1-micro): $7-15
- Cloud Storage: <$1 (for ~1000 policies)
- Networking: $1-5

**Total: ~$15-40/month** for pilot volume (20 policies)

## Troubleshooting

### Common Issues

**1. Database Connection Errors**
```bash
# Check Cloud SQL is running
gcloud sql instances describe travel-rpa-db

# Verify Cloud Run has Cloud SQL access
gcloud run services describe travel-rpa --region=us-central1 | grep cloudsql
```

**2. Authentication Errors (401 Unauthorized)**
```bash
# Verify webhook secret matches
gcloud secrets versions access latest --secret="N8N_WEBHOOK_SECRET"

# Check n8n environment variable
```

**3. Timeout Errors**
```bash
# Increase Cloud Run timeout
gcloud run services update travel-rpa \
  --timeout=600 \
  --region=us-central1
```

**4. Out of Memory Errors**
```bash
# Increase memory allocation
gcloud run services update travel-rpa \
  --memory=4Gi \
  --region=us-central1
```

## Security Checklist

- [ ] Database password is strong and stored in Secret Manager
- [ ] Django SECRET_KEY is random and stored in Secret Manager
- [ ] N8N_WEBHOOK_SECRET matches between Django and n8n
- [ ] Cloud SQL has no public IP (Cloud Run connects via Unix socket)
- [ ] Cloud Storage buckets have appropriate lifecycle rules
- [ ] Service accounts follow principle of least privilege
- [ ] Logs don't contain PII (passport numbers, names)
- [ ] HTTPS is enforced (Cloud Run default)

## Next Steps

1. **Load Testing**: Use Apache Bench or Locust to test with 50 concurrent requests
2. **Golden Set Testing**: Run all 20 golden test cases end-to-end via n8n
3. **Monitoring Setup**: Configure dashboards in Cloud Monitoring
4. **Backup Strategy**: Set up automated Cloud SQL backups
5. **CI/CD**: Set up GitHub Actions for automated deployments
6. **Documentation**: Update n8n workflow documentation with screenshots

## Rollback Procedure

If deployment fails or issues arise:

```bash
# List revisions
gcloud run revisions list --service=travel-rpa --region=us-central1

# Rollback to previous revision
gcloud run services update-traffic travel-rpa \
  --to-revisions=travel-rpa-00001-xxx=100 \
  --region=us-central1
```

## Support

For issues or questions:
- Check Cloud Run logs first: `gcloud run services logs tail travel-rpa --region=us-central1`
- Review Django logs in Cloud Logging
- Test endpoints manually with curl:
  ```bash
  curl -X POST https://travel-rpa-xxxxx-uc.a.run.app/api/v1/ingest \
    -H "X-Webhook-Secret: YOUR_SECRET" \
    -H "Content-Type: application/json" \
    -d @travel_rpa/tests/golden/case_06_outbound_silver_10days/email.json
  ```
