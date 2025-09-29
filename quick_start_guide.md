# Travel Policy Automation - Quick Start Guide

## 🚀 Phase 1: Core System Setup (Start Here)

### Step 1: Environment Setup (30 minutes)
```bash
# Create project directory
mkdir travel_policy_automation
cd travel_policy_automation

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create basic structure
mkdir -p {src,data,config,tests}
```

### Step 2: Install Core Dependencies (15 minutes)
```bash
# Install essential packages first
pip install python-dotenv imaplib2 pydantic requests beautifulsoup4 pandas pyyaml

# Install NLP packages
pip install spacy transformers
python -m spacy download en_core_web_sm

# Install OCR packages
pip install pytesseract Pillow opencv-python

# Save requirements
pip freeze > requirements.txt
```

### Step 3: Create Basic Email Monitor (45 minutes)
Create `src/email_monitor.py` with basic IMAP connection and test with hello@limitless-tech.ai

### Step 4: Test Email Connection (15 minutes)
```python
# Quick test script
from src.email_monitor import EmailMonitor

monitor = EmailMonitor()
emails = monitor.check_for_new_emails()
print(f"Found {len(emails)} emails")
```

## 🎯 Why This Order Works:

### ✅ **Start with Python (Not n8n) Because:**
1. **Immediate Testing** - You can test logic with sample emails right away
2. **Debugging Ease** - Python errors are easier to debug than n8n workflow issues
3. **Core Functionality** - The automation logic is in Python, n8n just triggers it
4. **Independence** - Can run standalone without external dependencies

### ❌ **Don't Start with n8n Because:**
1. **No Logic to Trigger** - n8n needs working Python components to call
2. **Black Box Testing** - Harder to debug when email processing fails
3. **Platform Dependency** - Adds external service complexity early
4. **Workflow Overhead** - Time spent on workflow design vs core functionality

## 📋 **Today's Action Plan (2-3 hours):**

### Hour 1: Setup & Email Connection
- [ ] Create project structure
- [ ] Install core dependencies
- [ ] Set up email credentials in .env
- [ ] Test IMAP connection to hello@limitless-tech.ai

### Hour 2: Basic Email Processing
- [ ] Build email parsing function
- [ ] Test with one sample email
- [ ] Extract basic text content
- [ ] Log email processing results

### Hour 3: Simple Intent Detection
- [ ] Create basic keyword matching
- [ ] Test with "travel policy" phrases
- [ ] Return "issue_travel_policy" or "other"
- [ ] Test with 3-4 sample emails

## 🔧 **Minimal Viable Product (MVP) - End of Day 1:**

```python
# This should work by end of today:
def process_email_mvp(email_content):
    # 1. Detect if it's a travel policy request
    if "travel policy" in email_content.lower():
        print("✅ Travel policy request detected")
        
        # 2. Extract basic info (regex patterns)
        if "outbound" in email_content.lower():
            print("✅ Outbound travel detected")
        
        return "PROCESS"
    else:
        print("❌ Not a travel policy request")
        return "IGNORE"
```

## 🎯 **Success Metrics for Day 1:**
- [ ] Email connection working
- [ ] Can read sample emails
- [ ] Basic intent detection (keyword matching)
- [ ] Processed 3+ test scenarios
- [ ] Logged results for review

## 🚨 **Red Flags to Avoid:**
- ❌ Don't spend time on n8n UI/workflows yet
- ❌ Don't try to implement all NLP features at once
- ❌ Don't focus on perfect OCR before basic email works
- ❌ Don't build complex premium calculations before data extraction works

## 📞 **When to Move to n8n (Day 3-4):**
Only after you have:
- ✅ Working email monitoring
- ✅ Basic intent detection
- ✅ Field extraction (even if basic)
- ✅ Can process 5+ sample emails successfully
- ✅ Core Python automation runs end-to-end

## 🎯 **Next Phase Triggers:**
- **Phase 2 (OCR):** When basic email processing works
- **Phase 3 (n8n):** When you have working Python components to orchestrate
- **Phase 4 (Testing):** When end-to-end flow works manually

This approach ensures you have working components before adding orchestration complexity.