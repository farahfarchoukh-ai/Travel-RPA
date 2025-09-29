#!/usr/bin/env python3
"""
Travel Policy Automation - Infrastructure Setup Script
Simplified version for CEO requirements
"""

import os
import sys
import subprocess
import json
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_directory_structure():
    """Create required directory structure"""
    logger.info("🏗️ Creating directory structure...")
    
    required_dirs = [
        'data/policy_pdfs/templates',
        'data/policy_pdfs/generated', 
        'data/policy_pdfs/samples',
        'data/knowledge_base',
        'data/attachments/passports',
        'data/attachments/documents',
        'logs',
        'src',
        'config',
        'tests/test_scenarios',
        'mock_backend',
        'n8n_workflows'
    ]
    
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Created: {dir_path}")
    
    return True

def create_env_file():
    """Create environment configuration file"""
    logger.info("⚙️ Creating environment configuration...")
    
    env_content = """# Travel Policy Automation - Environment Configuration

# Email Configuration
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_USERNAME=hello@limitless-tech.ai
EMAIL_PASSWORD=your_app_password_here
LIMITLESS_EMAIL=your_limitless_email_here
LIMITLESS_PASSWORD=your_limitless_password_here

# API Keys
OPENAI_API_KEY=your_openai_api_key_here

# OCR Configuration
TESSERACT_PATH=/usr/bin/tesseract
OCR_CONFIDENCE_THRESHOLD=60

# n8n Configuration
N8N_WEBHOOK_URL=https://your-n8n-instance.app.n8n.cloud/webhook/travel-policy

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
"""
    
    with open(".env", 'w') as f:
        f.write(env_content)
    
    logger.info("✅ Created .env file")
    return True

def create_knowledge_base():
    """Create sample knowledge base files"""
    logger.info("📚 Creating sample knowledge base...")
    
    # Create tariffs.csv
    tariffs_content = """travel_direction,geographic_scope,class_of_cover,base_rate,daily_rate
outbound,worldwide,economy,50,5
outbound,worldwide,business,75,8
outbound,worldwide,first,100,12
outbound,worldwide_excluding_us_canada,economy,35,4
outbound,worldwide_excluding_us_canada,business,55,6
outbound,worldwide_excluding_us_canada,first,75,9
inbound,domestic,economy,25,3
inbound,domestic,business,40,5
inbound,domestic,first,60,8"""
    
    with open("data/knowledge_base/tariffs.csv", 'w') as f:
        f.write(tariffs_content)
    
    # Create rules.yml
    rules_content = """# Travel Policy Pricing Rules

discounts:
  multi_traveller:
    "2-5": 0.05    # 5% discount for 2-5 travellers
    "6-10": 0.10   # 10% discount for 6-10 travellers
    "11+": 0.15    # 15% discount for 11+ travellers
  
  long_term:
    "30-60": 0.05  # 5% discount for 30-60 days
    "61-90": 0.10  # 10% discount for 61-90 days
    "91+": 0.15    # 15% discount for 91+ days

surcharges:
  high_risk_countries: 0.25
  last_minute: 0.20
  elderly: 0.15

limits:
  minimum_premium: 25
  maximum_premium: 5000"""
    
    with open("data/knowledge_base/rules.yml", 'w') as f:
        f.write(rules_content)
    
    logger.info("✅ Created knowledge base files")
    return True

def create_mock_backend():
    """Create simple mock backend"""
    logger.info("🖥️ Creating mock backend...")
    
    mock_app = '''#!/usr/bin/env python3
"""
Simple Mock Backend for Travel Policy Simulation
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)

policies_db = {}

@app.route('/')
def home():
    return """
    <h1>Travel Policy Management System</h1>
    <p>Mock Backend for Automation Testing</p>
    <p><a href="/login">Login to System</a></p>
    """

@app.route('/login')
def login():
    return """
    <h2>Login Successful</h2>
    <p>Welcome to the Policy Management System</p>
    <p>Demo User: demo_user</p>
    <p><a href="/dashboard">Go to Dashboard</a></p>
    """

@app.route('/dashboard')
def dashboard():
    return """
    <h2>Policy Dashboard</h2>
    <p>Policy Issuance System Ready</p>
    <p>Policies Issued: {}</p>
    """.format(len(policies_db))

@app.route('/api/issue_policy', methods=['POST'])
def issue_policy():
    """Simulate policy issuance"""
    policy_data = request.json or {}
    policy_reference = f"POL-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    policy_record = {
        'policy_reference': policy_reference,
        'status': 'ISSUED',
        'created_at': datetime.now().isoformat(),
        **policy_data
    }
    
    policies_db[policy_reference] = policy_record
    
    return jsonify({
        'success': True,
        'policy_reference': policy_reference,
        'status': 'ISSUED'
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'policies_count': len(policies_db)
    })

if __name__ == '__main__':
    print("🚀 Starting Mock Backend...")
    app.run(host='0.0.0.0', port=5000, debug=True)
'''
    
    with open("mock_backend/app.py", 'w') as f:
        f.write(mock_app)
    
    # Create startup script
    startup_script = '''#!/bin/bash
echo "🚀 Starting Travel Policy Mock Backend..."
cd mock_backend
python3 app.py
'''
    
    with open("mock_backend/start_backend.sh", 'w') as f:
        f.write(startup_script)
    
    os.chmod("mock_backend/start_backend.sh", 0o755)
    
    logger.info("✅ Created mock backend")
    return True

def create_n8n_workflow():
    """Create n8n workflow template"""
    logger.info("🔄 Creating n8n workflow...")
    
    workflow = {
        "name": "Travel Policy Automation",
        "nodes": [
            {
                "name": "Email Trigger",
                "type": "n8n-nodes-base.emailReadImap",
                "position": [250, 300]
            },
            {
                "name": "Process Email",
                "type": "n8n-nodes-base.executeCommand",
                "position": [450, 300]
            },
            {
                "name": "Issue Policy",
                "type": "n8n-nodes-base.httpRequest",
                "position": [650, 300]
            }
        ]
    }
    
    with open("n8n_workflows/travel_policy_workflow.json", 'w') as f:
        json.dump(workflow, f, indent=2)
    
    logger.info("✅ Created n8n workflow template")
    return True

def install_basic_dependencies():
    """Install essential dependencies"""
    logger.info("📦 Installing basic dependencies...")
    
    try:
        # Install Flask for mock backend
        subprocess.run([sys.executable, "-m", "pip", "install", "flask", "flask-cors"], 
                      check=True, capture_output=True)
        logger.info("✅ Installed Flask for mock backend")
        
        # Install basic packages
        subprocess.run([sys.executable, "-m", "pip", "install", "python-dotenv", "pyyaml", "requests"], 
                      check=True, capture_output=True)
        logger.info("✅ Installed basic utilities")
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        return False

def main():
    """Run infrastructure setup"""
    logger.info("🚀 Starting Infrastructure Setup for CEO Requirements")
    print("="*60)
    
    steps = [
        ("Creating directory structure", create_directory_structure),
        ("Installing basic dependencies", install_basic_dependencies),
        ("Creating environment file", create_env_file),
        ("Creating knowledge base", create_knowledge_base),
        ("Creating mock backend", create_mock_backend),
        ("Creating n8n workflow template", create_n8n_workflow)
    ]
    
    for step_name, step_func in steps:
        logger.info(f"📋 {step_name}...")
        if not step_func():
            logger.error(f"❌ Failed: {step_name}")
            return False
        logger.info(f"✅ Completed: {step_name}")
    
    print("\n" + "="*60)
    print("🎉 INFRASTRUCTURE SETUP COMPLETE!")
    print("="*60)
    print("\n📋 NEXT STEPS:")
    print("\n1. 📧 Configure Email Credentials in .env file")
    print("2. 🔑 Add OpenAI API key to .env file")
    print("3. 🌐 Create n8n account at https://app.n8n.cloud")
    print("4. 🖥️  Start mock backend: ./mock_backend/start_backend.sh")
    print("5. 🧪 Test system components")
    print("\n📞 Ready for CEO progress review!")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)