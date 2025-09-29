# Travel Policy Automation - Infrastructure Setup

## 🏗️ Infrastructure Components Setup

### 1. Email Inbox Configuration

#### A. Primary Email Setup (hello@limitless-tech.ai)
```bash
# Email server configuration
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=hello@limitless-tech.ai
EMAIL_PASSWORD=<app-specific-password>
```

#### B. Limitless Email Configuration (for team access)
```bash
# Secondary email for development/testing
LIMITLESS_EMAIL=<your-limitless-email>
LIMITLESS_PASSWORD=<app-specific-password>
```

### 2. RPA Tool Setup (n8n)

#### A. n8n Cloud Account Setup
- URL: https://app.n8n.cloud
- Account: Register with your limitless email
- Billing: Use provided credit card
- Plan: Starter plan ($20/month) for pilot

#### B. n8n Local Development (Optional)
```bash
# Install n8n locally for development
npm install -g n8n
export N8N_BASIC_AUTH_ACTIVE=true
export N8N_BASIC_AUTH_USER=admin
export N8N_BASIC_AUTH_PASSWORD=admin123
n8n start
```

### 3. OCR/NLP Services Configuration

#### A. Local OCR Setup (Tesseract)
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr
sudo apt-get install libtesseract-dev

# macOS
brew install tesseract

# Verify installation
tesseract --version
```

#### B. NLP Services Setup
```bash
# Install spaCy and models
pip install spacy
python -m spacy download en_core_web_sm
python -m spacy download en_core_web_md

# Install OpenAI for enhanced NLP
pip install openai
export OPENAI_API_KEY=<your-openai-key>
```

#### C. Cloud OCR Services (Backup)
```bash
# Google Cloud Vision API
pip install google-cloud-vision
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"

# AWS Textract (Alternative)
pip install boto3
export AWS_ACCESS_KEY_ID=<your-access-key>
export AWS_SECRET_ACCESS_KEY=<your-secret-key>
```

### 4. Policy PDF Directory Structure

#### A. Directory Setup
```bash
mkdir -p data/policy_pdfs/{templates,generated,samples}
mkdir -p data/attachments/{passports,documents}
mkdir -p data/knowledge_base
```

#### B. Sample Policy Templates
- Location: `data/policy_pdfs/templates/`
- Files needed:
  - `outbound_worldwide_template.pdf`
  - `outbound_excluding_us_canada_template.pdf`
  - `inbound_domestic_template.pdf`

### 5. Mock Backend Setup

#### A. Policy Issuance System Simulation
```bash
# Create mock web application
mkdir -p mock_backend
cd mock_backend

# Simple Flask application for demo
pip install flask selenium webdriver-manager
```

## 🔧 Complete Setup Scripts

### Environment Configuration (.env)
```env
# Email Configuration
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_USERNAME=hello@limitless-tech.ai
EMAIL_PASSWORD=your_app_password
LIMITLESS_EMAIL=your_limitless_email
LIMITLESS_PASSWORD=your_limitless_password

# API Keys
OPENAI_API_KEY=your_openai_api_key
GOOGLE_CLOUD_KEY_PATH=path/to/google-credentials.json

# OCR Configuration
TESSERACT_PATH=/usr/bin/tesseract
OCR_CONFIDENCE_THRESHOLD=60

# n8n Configuration
N8N_WEBHOOK_URL=https://your-n8n-instance.app.n8n.cloud/webhook/travel-policy
N8N_API_KEY=your_n8n_api_key

# Mock Backend
MOCK_BACKEND_URL=http://localhost:5000
MOCK_LOGIN_USER=demo_user
MOCK_LOGIN_PASSWORD=demo_password

# File Paths
POLICY_PDF_DIR=./data/policy_pdfs
KNOWLEDGE_BASE_DIR=./data/knowledge_base
ATTACHMENTS_DIR=./data/attachments

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/automation.log
```

### Infrastructure Test Script
```python
#!/usr/bin/env python3
"""
Infrastructure Test Script
Tests all infrastructure components
"""

import os
import sys
from pathlib import Path
import logging

def test_email_connection():
    """Test email server connectivity"""
    print("🔧 Testing email connection...")
    try:
        import imaplib
        import smtplib
        
        # Test IMAP connection
        imap = imaplib.IMAP4_SSL('imap.gmail.com')
        print("✅ IMAP server reachable")
        
        # Test SMTP connection
        smtp = smtplib.SMTP('smtp.gmail.com', 587)
        smtp.starttls()
        print("✅ SMTP server reachable")
        
        return True
    except Exception as e:
        print(f"❌ Email connection failed: {e}")
        return False

def test_ocr_setup():
    """Test OCR capabilities"""
    print("🔧 Testing OCR setup...")
    try:
        import pytesseract
        from PIL import Image
        import numpy as np
        
        # Test Tesseract installation
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract version: {version}")
        
        # Test basic OCR
        test_image = Image.new('RGB', (200, 50), color='white')
        result = pytesseract.image_to_string(test_image)
        print("✅ OCR processing works")
        
        return True
    except Exception as e:
        print(f"❌ OCR setup failed: {e}")
        return False

def test_nlp_setup():
    """Test NLP capabilities"""
    print("🔧 Testing NLP setup...")
    try:
        import spacy
        
        # Test spaCy model loading
        nlp = spacy.load("en_core_web_sm")
        doc = nlp("I need to issue a travel policy")
        print(f"✅ spaCy model loaded, processed {len(doc)} tokens")
        
        # Test OpenAI connection (if API key available)
        if os.getenv('OPENAI_API_KEY'):
            import openai
            print("✅ OpenAI API key configured")
        
        return True
    except Exception as e:
        print(f"❌ NLP setup failed: {e}")
        return False

def test_directory_structure():
    """Test required directories exist"""
    print("🔧 Testing directory structure...")
    required_dirs = [
        'data/policy_pdfs/templates',
        'data/policy_pdfs/generated',
        'data/policy_pdfs/samples',
        'data/knowledge_base',
        'data/attachments/passports',
        'logs'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path}")
        else:
            print(f"❌ {dir_path} - creating...")
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            all_exist = False
    
    return all_exist

def test_mock_backend():
    """Test mock backend accessibility"""
    print("🔧 Testing mock backend...")
    try:
        import requests
        
        # Test if mock backend is running
        mock_url = os.getenv('MOCK_BACKEND_URL', 'http://localhost:5000')
        try:
            response = requests.get(f"{mock_url}/health", timeout=5)
            print("✅ Mock backend is running")
            return True
        except requests.exceptions.ConnectionError:
            print("⚠️  Mock backend not running (will start later)")
            return True
    except Exception as e:
        print(f"❌ Mock backend test failed: {e}")
        return False

def main():
    """Run all infrastructure tests"""
    print("🚀 Travel Policy Automation - Infrastructure Test")
    print("=" * 50)
    
    tests = [
        ("Email Connection", test_email_connection),
        ("OCR Setup", test_ocr_setup),
        ("NLP Setup", test_nlp_setup),
        ("Directory Structure", test_directory_structure),
        ("Mock Backend", test_mock_backend)
    ]
    
    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()
        print()
    
    print("📊 Infrastructure Test Results:")
    print("=" * 30)
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All infrastructure components ready!")
        return True
    else:
        print("⚠️  Some infrastructure components need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

## 📋 Infrastructure Setup Checklist

### ✅ Phase 1: Basic Setup (30 minutes)
- [ ] Create project directory structure
- [ ] Set up Python virtual environment
- [ ] Install core dependencies
- [ ] Create .env configuration file

### ✅ Phase 2: Email Infrastructure (20 minutes)
- [ ] Configure hello@limitless-tech.ai IMAP/SMTP
- [ ] Set up app-specific passwords
- [ ] Test email connectivity
- [ ] Configure limitless email backup

### ✅ Phase 3: RPA Tool (n8n) (30 minutes)
- [ ] Create n8n cloud account with limitless email
- [ ] Set up billing with provided credit card
- [ ] Create basic webhook endpoint
- [ ] Test n8n connectivity

### ✅ Phase 4: OCR/NLP Services (25 minutes)
- [ ] Install Tesseract OCR
- [ ] Install spaCy and download models
- [ ] Configure OpenAI API key
- [ ] Test OCR with sample image

### ✅ Phase 5: File Structure (15 minutes)
- [ ] Create policy PDF directories
- [ ] Set up knowledge base folder
- [ ] Create attachment processing folders
- [ ] Add sample policy templates

### ✅ Phase 6: Mock Backend (30 minutes)
- [ ] Create Flask mock application
- [ ] Set up basic login simulation
- [ ] Create policy issuance endpoints
- [ ] Test backend accessibility

## 🎯 Success Criteria
After setup, you should have:
- ✅ Email inbox monitoring capability
- ✅ n8n account with webhook ready
- ✅ OCR processing for passport images
- ✅ NLP for intent detection
- ✅ File system for policy management
- ✅ Mock backend for system simulation

Total Setup Time: **~2.5 hours**