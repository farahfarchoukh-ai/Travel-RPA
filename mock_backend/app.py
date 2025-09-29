#!/usr/bin/env python3
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
        .policies-list { margin-top: 30px; }
        .policy-item { background: #fff; border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 4px; }
        .policy-status { padding: 4px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; }
        .status-issued { background-color: #d4edda; color: #155724; }
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
                        <span class="policy-status status-issued">ISSUED</span>
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
        policy_data = request.json or {}
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
    logger.info("🚀 Starting Mock Backend for Travel Policy Automation")
    app.run(host='0.0.0.0', port=5000, debug=True)