#!/usr/bin/env python3
"""
Travel Policy Automation - Infrastructure Setup Script
Automates the complete infrastructure setup process
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InfrastructureSetup:
    """Automated infrastructure setup for travel policy automation"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.required_dirs = [
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
        
    def create_directory_structure(self):
        """Create required directory structure"""
        logger.info("🏗️ Creating directory structure...")
        
        for dir_path in self.required_dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created: {dir_path}")
        
        return True
    
    def install_dependencies(self):
        """Install all required Python dependencies"""
        logger.info("📦 Installing Python dependencies...")
        
        requirements = [
            # Core dependencies
            "python-dotenv==1.0.0",
            "pydantic==2.5.0",
            "requests==2.31.0",
            
            # Email handling
            "imaplib2==3.6",
            "email-validator==2.1.0",
            
            # NLP and AI
            "openai==1.3.0",
            "spacy==3.7.0",
            "transformers==4.36.0",
            
            # OCR
            "pytesseract==0.3.10",
            "Pillow==10.1.0",
            "opencv-python==4.8.1.78",
            
            # Data processing
            "pandas==2.1.4",
            "numpy==1.24.3",
            "pyyaml==6.0.1",
            
            # Web automation
            "selenium==4.15.0",
            "webdriver-manager==4.15.1",
            
            # PDF handling
            "reportlab==4.0.7",
            "PyPDF2==3.0.1",
            
            # Utilities
            "python-dateutil==2.8.2",
            "fuzzywuzzy==0.18.0",
            
            # Testing
            "pytest==7.4.3",
            
            # Mock backend
            "flask==3.0.0",
            "flask-cors==4.0.0"
        ]
        
        try:
            for package in requirements:
                subprocess.run([sys.executable, "-m", "pip", "install", package], 
                             check=True, capture_output=True)
                logger.info(f"✅ Installed: {package}")
            
            # Install spaCy model
            subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], 
                         check=True, capture_output=True)
            logger.info("✅ Installed spaCy English model")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install dependencies: {e}")
            return False
    
    def create_env_file(self):
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
GOOGLE_CLOUD_KEY_PATH=path/to/google-credentials.json

# OCR Configuration
TESSERACT_PATH=/usr/bin/tesseract
OCR_CONFIDENCE_THRESHOLD=60

# n8n Configuration
N8N_WEBHOOK_URL=https://your-n8n-instance.app.n8n.cloud/webhook/travel-policy
N8N_API_KEY=your_n8n_api_key_here

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

# System Configuration
MAX_EMAIL_PROCESSING_TIME=300
EMAIL_CHECK_INTERVAL=30
RETRY_ATTEMPTS=3
"""
        
        env_path = self.project_root / ".env"
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        logger.info("✅ Created .env file (please update with actual credentials)")
        return True
    
    def create_sample_knowledge_base(self):
        """Create sample knowledge base files"""
        logger.info("📚 Creating sample knowledge base...")
        
        # Create sample tariffs.csv
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
        
        tariffs_path = self.project_root / "data/knowledge_base/tariffs.csv"
        with open(tariffs_path, 'w') as f:
            f.write(tariffs_content)
        
        # Create sample rules.yml
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
  high_risk_countries: 0.25  # 25% surcharge for high-risk destinations
  last_minute: 0.20          # 20% surcharge for bookings within 7 days
  elderly: 0.15              # 15% surcharge for travellers over 70

limits:
  minimum_premium: 25
  maximum_premium: 5000
  max_trip_duration: 365
  max_travellers: 50

coverage_limits:
  medical_expenses: 1000000
  trip_cancellation: 10000
  baggage_loss: 2500
  personal_liability: 2000000"""
        
        rules_path = self.project_root / "data/knowledge_base/rules.yml"
        with open(rules_path, 'w') as f:
            f.write(rules_content)
        
        logger.info("✅ Created sample knowledge base files")
        return True
    
    def create_mock_backend(self):
        """Create mock backend for policy issuance simulation"""
        logger.info("🖥️ Creating mock backend...")
        
        mock_backend_code = '''#!/usr/bin/env python3
"""
Mock Backend for Travel Policy Issuance Simulation
Simulates a policy management system for testing
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import uuid
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock database
policies_db = {}
sessions = {}

# HTML template for mock login page
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Travel Policy Management System - Login</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
        .container { max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="text"], input[type="password"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { background-color: #007bff; color: white; padding: 12px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%; font-size: 16px; }
        button:hover { background-color: #0056b3; }
        .header { text-align: center; margin-bottom: 30px; }
        .status { padding: 10px; margin-bottom: 20px; border-radius: 4px; }
        .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Travel Policy Management System</h2>
            <p>Mock Backend for Automation Testing</p>
        </div>
        
        {% if message %}
        <div class="status {{ message_type }}">{{ message }}</div>
        {% endif %}
        
        <form method="POST" action="/login">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" value="demo_user" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" value="demo_password" required>
            </div>
            
            <button type="submit">Login to Policy System</button>
        </form>
        
        <div style="margin-top: 20px; font-size: 12px; color: #666; text-align: center;">
            <p>Demo Credentials: demo_user / demo_password</p>
        </div>
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Policy Management Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { border-bottom: 1px solid #eee; padding-bottom: 20px; margin-bottom: 30px; }
        .policy-form { background: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 30px; }
        .form-row { display: flex; gap: 20px; margin-bottom: 15px; }
        .form-group { flex: 1; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { background-color: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; }
        button:hover { background-color: #218838; }
        .logout-btn { background-color: #dc3545; }
        .logout-btn:hover { background-color: #c82333; }
        .policies-list { margin-top: 30px; }
        .policy-item { background: #fff; border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 4px; }
        .policy-status { padding: 4px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; }
        .status-issued { background-color: #d4edda; color: #155724; }
        .status-pending { background-color: #fff3cd; color: #856404; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Travel Policy Management Dashboard</h2>
            <p>Welcome, {{ username }}! | <a href="/logout">Logout</a></p>
        </div>
        
        <div class="policy-form">
            <h3>Issue New Travel Policy</h3>
            <form id="policyForm">
                <div class="form-row">
                    <div class="form-group">
                        <label>Travel Direction:</label>
                        <select id="travelDirection">
                            <option value="outbound">Outbound</option>
                            <option value="inbound">Inbound</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Geographic Scope:</label>
                        <select id="geographicScope">
                            <option value="worldwide">Worldwide</option>
                            <option value="worldwide_excluding_us_canada">Worldwide Excluding US/Canada</option>
                            <option value="domestic">Domestic</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Class of Cover:</label>
                        <select id="classOfCover">
                            <option value="economy">Economy</option>
                            <option value="business">Business</option>
                            <option value="first">First Class</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label>Number of Days:</label>
                        <input type="number" id="numberOfDays" min="1" max="365" value="7">
                    </div>
                    <div class="form-group">
                        <label>Number of Travellers:</label>
                        <input type="number" id="numberOfTravellers" min="1" max="50" value="1">
                    </div>
                    <div class="form-group">
                        <label>Travel Date:</label>
                        <input type="date" id="travelDate">
                    </div>
                </div>
                
                <button type="button" onclick="issuePolicy()">Issue Policy</button>
                <button type="button" onclick="simulateProcessing()" style="background-color: #17a2b8;">Simulate Processing</button>
            </form>
        </div>
        
        <div class="policies-list">
            <h3>Recent Policies</h3>
            <div id="policiesList">
                <!-- Policies will be loaded here -->
            </div>
        </div>
    </div>
    
    <script>
        function issuePolicy() {
            const policyData = {
                travel_direction: document.getElementById('travelDirection').value,
                geographic_scope: document.getElementById('geographicScope').value,
                class_of_cover: document.getElementById('classOfCover').value,
                number_of_days: parseInt(document.getElementById('numberOfDays').value),
                number_of_travellers: parseInt(document.getElementById('numberOfTravellers').value),
                travel_date: document.getElementById('travelDate').value
            };
            
            fetch('/api/issue_policy', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(policyData)
            })
            .then(response => response.json())
            .then(data => {
                alert('Policy issued successfully! Reference: ' + data.policy_reference);
                loadPolicies();
            })
            .catch(error => {
                alert('Error issuing policy: ' + error);
            });
        }
        
        function simulateProcessing() {
            alert('Simulating policy processing workflow...');
            setTimeout(() => {
                alert('Policy processing simulation completed!');
            }, 2000);
        }
        
        function loadPolicies() {
            fetch('/api/policies')
            .then(response => response.json())
            .then(policies => {
                const policiesHtml = policies.map(policy => `
                    <div class="policy-item">
                        <strong>Policy: ${policy.policy_reference}</strong>
                        <span class="policy-status status-${policy.status.toLowerCase()}">${policy.status}</span>
                        <br>
                        <small>Travel: ${policy.travel_direction} | ${policy.geographic_scope} | ${policy.class_of_cover}</small>
                        <br>
                        <small>Created: ${new Date(policy.created_at).toLocaleString()}</small>
                    </div>
                `).join('');
                document.getElementById('policiesList').innerHTML = policiesHtml;
            });
        }
        
        // Load policies on page load
        loadPolicies();
    </script>
</body>
</html>
"""

@app.route('/')
def login_page():
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == 'demo_user' and password == 'demo_password':
        session_id = str(uuid.uuid4())
        sessions[session_id] = {'username': username, 'logged_in': True}
        
        logger.info(f"User {username} logged in successfully")
        return render_template_string(DASHBOARD_TEMPLATE, username=username)
    else:
        return render_template_string(LOGIN_TEMPLATE, 
                                    message="Invalid credentials", 
                                    message_type="error")

@app.route('/logout')
def logout():
    return render_template_string(LOGIN_TEMPLATE, 
                                message="Logged out successfully", 
                                message_type="success")

@app.route('/api/issue_policy', methods=['POST'])
def issue_policy():
    """Simulate policy issuance"""
    try:
        policy_data = request.json
        policy_reference = f"POL-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        policy_record = {
            'policy_reference': policy_reference,
            'status': 'ISSUED',
            'created_at': datetime.now().isoformat(),
            **policy_data
        }
        
        policies_db[policy_reference] = policy_record
        
        logger.info(f"Policy issued: {policy_reference}")
        
        return jsonify({
            'success': True,
            'policy_reference': policy_reference,
            'status': 'ISSUED',
            'message': 'Policy issued successfully'
        })
        
    except Exception as e:
        logger.error(f"Error issuing policy: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/policies', methods=['GET'])
def get_policies():
    """Get all policies"""
    policies_list = list(policies_db.values())
    policies_list.sort(key=lambda x: x['created_at'], reverse=True)
    return jsonify(policies_list[:10])  # Return last 10 policies

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'policies_count': len(policies_db)
    })

if __name__ == '__main__':
    logger.info("Starting Mock Backend for Travel Policy Automation")
    app.run(host='0.0.0.0', port=5000, debug=True)
'''
        
        mock_backend_path = self.project_root / "mock_backend/app.py"
        with open(mock_backend_path, 'w') as f:
            f.write(mock_backend_code)
        
        # Create startup script
        startup_script = '''#!/bin/bash
# Mock Backend Startup Script

echo "🚀 Starting Travel Policy Mock Backend..."
cd mock_backend
python3 app.py
'''
        
        startup_path = self.project_root / "mock_backend/start_backend.sh"
        with open(startup_path, 'w') as f:
            f.write(startup_script)
        
        # Make startup script executable
        os.chmod(startup_path, 0o755)
        
        logger.info("✅ Created mock backend application")
        return True
    
    def create_n8n_workflow(self):
        """Create n8n workflow template"""
        logger.info("🔄 Creating n8n workflow template...")
        
        workflow = {
            "name": "Travel Policy Automation Workflow",
            "nodes": [
                {
                    "parameters": {
                        "pollTimes": {
                            "item": [{"mode": "everyMinute"}]
                        },
                        "options": {}
                    },
                    "name": "Email Trigger",
                    "type": "n8n-nodes-base.emailReadImap",
                    "position": [250, 300],
                    "credentials": {
                        "imap": {
                            "id": "travel_policy_email",
                            "name": "Travel Policy Email Account"
                        }
                    }
                },
                {
                    "parameters": {
                        "command": "python3 /workspace/main.py --process-email",
                        "additionalFields": {
                            "workingDirectory": "/workspace"
                        }
                    },
                    "name": "Process Travel Policy Request",
                    "type": "n8n-nodes-base.executeCommand",
                    "position": [450, 300]
                },
                {
                    "parameters": {
                        "requestMethod": "POST",
                        "url": "http://localhost:5000/api/issue_policy",
                        "sendBody": True,
                        "bodyContentType": "json",
                        "jsonBody": "={{ $json }}"
                    },
                    "name": "Issue Policy in Backend",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [650, 300]
                },
                {
                    "parameters": {
                        "fromEmail": "hello@limitless-tech.ai",
                        "toEmail": "={{ $json.recipient_email }}",
                        "subject": "Travel Policy Issued - {{ $json.policy_reference }}",
                        "emailFormat": "html",
                        "message": "Your travel policy has been issued successfully.",
                        "attachments": "={{ $json.policy_pdf }}"
                    },
                    "name": "Send Policy Email",
                    "type": "n8n-nodes-base.emailSend",
                    "position": [850, 300]
                }
            ],
            "connections": {
                "Email Trigger": {
                    "main": [[{"node": "Process Travel Policy Request", "type": "main", "index": 0}]]
                },
                "Process Travel Policy Request": {
                    "main": [[{"node": "Issue Policy in Backend", "type": "main", "index": 0}]]
                },
                "Issue Policy in Backend": {
                    "main": [[{"node": "Send Policy Email", "type": "main", "index": 0}]]
                }
            }
        }
        
        workflow_path = self.project_root / "n8n_workflows/travel_policy_workflow.json"
        with open(workflow_path, 'w') as f:
            json.dump(workflow, f, indent=2)
        
        logger.info("✅ Created n8n workflow template")
        return True
    
    def run_infrastructure_test(self):
        """Run comprehensive infrastructure test"""
        logger.info("🧪 Running infrastructure tests...")
        
        test_script = self.project_root / "test_infrastructure.py"
        
        # Create the test script content (from infrastructure_setup.md)
        test_content = '''#!/usr/bin/env python3
"""
Infrastructure Test Script
Tests all infrastructure components
"""

import os
import sys
from pathlib import Path
import logging

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
            print(f"❌ {dir_path}")
            all_exist = False
    
    return all_exist

def test_dependencies():
    """Test Python dependencies are installed"""
    print("🔧 Testing Python dependencies...")
    
    required_packages = [
        'pytesseract', 'PIL', 'cv2', 'spacy', 
        'pandas', 'yaml', 'requests', 'flask'
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            if package == 'PIL':
                from PIL import Image
            elif package == 'cv2':
                import cv2
            elif package == 'yaml':
                import yaml
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            all_installed = False
    
    return all_installed

def test_knowledge_base():
    """Test knowledge base files exist"""
    print("🔧 Testing knowledge base files...")
    
    files_to_check = [
        'data/knowledge_base/tariffs.csv',
        'data/knowledge_base/rules.yml'
    ]
    
    all_exist = True
    for file_path in files_to_check:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            all_exist = False
    
    return all_exist

def main():
    """Run all infrastructure tests"""
    print("🚀 Travel Policy Automation - Infrastructure Test")
    print("=" * 50)
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Python Dependencies", test_dependencies),
        ("Knowledge Base Files", test_knowledge_base)
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
    
    print(f"\\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All infrastructure components ready!")
        return True
    else:
        print("⚠️  Some infrastructure components need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
'''
        
        with open(test_script, 'w') as f:
            f.write(test_content)
        
        # Make test script executable
        os.chmod(test_script, 0o755)
        
        # Run the test
        try:
            result = subprocess.run([sys.executable, str(test_script)], 
                                  capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print("Errors:", result.stderr)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to run infrastructure test: {e}")
            return False
    
    def setup_complete_infrastructure(self):
        """Run complete infrastructure setup"""
        logger.info("🚀 Starting complete infrastructure setup...")
        
        steps = [
            ("Creating directory structure", self.create_directory_structure),
            ("Installing dependencies", self.install_dependencies),
            ("Creating environment file", self.create_env_file),
            ("Creating knowledge base", self.create_sample_knowledge_base),
            ("Setting up mock backend", self.create_mock_backend),
            ("Creating n8n workflow", self.create_n8n_workflow),
            ("Running infrastructure test", self.run_infrastructure_test)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"📋 {step_name}...")
            if not step_func():
                logger.error(f"❌ Failed: {step_name}")
                return False
            logger.info(f"✅ Completed: {step_name}")
        
        logger.info("🎉 Infrastructure setup completed successfully!")
        self._print_next_steps()
        return True
    
    def _print_next_steps(self):
        """Print next steps for user"""
        print("\n" + "="*60)
        print("🎉 INFRASTRUCTURE SETUP COMPLETE!")
        print("="*60)
        print("\n📋 NEXT STEPS:")
        print("\n1. 📧 Configure Email Credentials:")
        print("   - Edit .env file with actual email passwords")
        print("   - Set up app-specific passwords for Gmail accounts")
        
        print("\n2. 🔑 Add API Keys:")
        print("   - Add OpenAI API key to .env file")
        print("   - Configure any cloud OCR service keys")
        
        print("\n3. 🌐 Set up n8n Account:")
        print("   - Create account at https://app.n8n.cloud")
        print("   - Import workflow from n8n_workflows/travel_policy_workflow.json")
        print("   - Configure email credentials in n8n")
        
        print("\n4. 🖥️  Start Mock Backend:")
        print("   - Run: ./mock_backend/start_backend.sh")
        print("   - Access at: http://localhost:5000")
        print("   - Test login: demo_user / demo_password")
        
        print("\n5. 🧪 Test the System:")
        print("   - Run: python test_infrastructure.py")
        print("   - Send test email to hello@limitless-tech.ai")
        print("   - Monitor logs in logs/automation.log")
        
        print("\n6. 🚀 Start Automation:")
        print("   - Run: python main.py")
        print("   - Monitor n8n workflow execution")
        
        print("\n" + "="*60)
        print("📞 Ready for CEO progress review on Oct 1st AM!")
        print("="*60)

def main():
    """Main setup function"""
    setup = InfrastructureSetup()
    success = setup.setup_complete_infrastructure()
    
    if success:
        logger.info("✅ Infrastructure setup completed successfully!")
        return 0
    else:
        logger.error("❌ Infrastructure setup failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
        
        startup_path = self.project_root / "mock_backend/start_backend.sh"
        with open(startup_path, 'w') as f:
            f.write(startup_script)
        
        # Make startup script executable
        os.chmod(startup_path, 0o755)
        
        logger.info("✅ Created mock backend application")
        return True
    
    def create_n8n_workflow(self):
        """Create n8n workflow template"""
        logger.info("🔄 Creating n8n workflow template...")
        
        workflow = {
            "name": "Travel Policy Automation Workflow",
            "nodes": [
                {
                    "parameters": {
                        "pollTimes": {
                            "item": [{"mode": "everyMinute"}]
                        },
                        "options": {}
                    },
                    "name": "Email Trigger",
                    "type": "n8n-nodes-base.emailReadImap",
                    "position": [250, 300],
                    "credentials": {
                        "imap": {
                            "id": "travel_policy_email",
                            "name": "Travel Policy Email Account"
                        }
                    }
                },
                {
                    "parameters": {
                        "command": "python3 /workspace/main.py --process-email",
                        "additionalFields": {
                            "workingDirectory": "/workspace"
                        }
                    },
                    "name": "Process Travel Policy Request",
                    "type": "n8n-nodes-base.executeCommand",
                    "position": [450, 300]
                },
                {
                    "parameters": {
                        "requestMethod": "POST",
                        "url": "http://localhost:5000/api/issue_policy",
                        "sendBody": True,
                        "bodyContentType": "json",
                        "jsonBody": "={{ $json }}"
                    },
                    "name": "Issue Policy in Backend",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [650, 300]
                },
                {
                    "parameters": {
                        "fromEmail": "hello@limitless-tech.ai",
                        "toEmail": "={{ $json.recipient_email }}",
                        "subject": "Travel Policy Issued - {{ $json.policy_reference }}",
                        "emailFormat": "html",
                        "message": "Your travel policy has been issued successfully.",
                        "attachments": "={{ $json.policy_pdf }}"
                    },
                    "name": "Send Policy Email",
                    "type": "n8n-nodes-base.emailSend",
                    "position": [850, 300]
                }
            ],
            "connections": {
                "Email Trigger": {
                    "main": [[{"node": "Process Travel Policy Request", "type": "main", "index": 0}]]
                },
                "Process Travel Policy Request": {
                    "main": [[{"node": "Issue Policy in Backend", "type": "main", "index": 0}]]
                },
                "Issue Policy in Backend": {
                    "main": [[{"node": "Send Policy Email", "type": "main", "index": 0}]]
                }
            }
        }
        
        workflow_path = self.project_root / "n8n_workflows/travel_policy_workflow.json"
        with open(workflow_path, 'w') as f:
            json.dump(workflow, f, indent=2)
        
        logger.info("✅ Created n8n workflow template")
        return True

def main():
    """Main setup function"""
    setup = InfrastructureSetup()
    success = setup.setup_complete_infrastructure()
    
    if success:
        logger.info("✅ Infrastructure setup completed successfully!")
        return 0
    else:
        logger.error("❌ Infrastructure setup failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())