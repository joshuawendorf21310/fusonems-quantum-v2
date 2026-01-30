#!/usr/bin/env python3
"""
FusionEMS Quantum - Deployment Verification Script
Tests connectivity, API health, and critical flows (Demo Request).
"""
import sys
import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def log(msg, status="INFO"):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{status}] {msg}")

def check_health():
    log("Checking Backend Health...")
    try:
        resp = requests.get(f"{BASE_URL}/healthz", timeout=5)
        if resp.status_code == 200:
            log("Backend is ONLINE", "SUCCESS")
        else:
            log(f"Backend returned {resp.status_code}", "FAIL")
            return False
    except requests.exceptions.ConnectionError:
        log("Backend Connection Refused", "FAIL")
        return False
    return True

def check_frontend():
    log("Checking Frontend Accessibility...")
    try:
        resp = requests.get(FRONTEND_URL, timeout=5)
        if resp.status_code == 200:
            log("Frontend is ONLINE", "SUCCESS")
        else:
            log(f"Frontend returned {resp.status_code}", "FAIL")
            return False
    except requests.exceptions.ConnectionError:
        log("Frontend Connection Refused", "FAIL")
        return False
    return True

def test_demo_request():
    log("Testing Demo Request Flow...")
    payload = {
        "name": "Deployment Test Bot",
        "email": "test-bot@fusionems.com",
        "organization": "Test Agency",
        "phone": "555-0199",
        "role": "ems-chief",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "pending",
        "source": "deployment_script"
    }
    
    try:
        resp = requests.post(
            f"{BASE_URL}/api/v1/demo-requests",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if resp.status_code in [200, 201]:
            log("Demo Request Submitted Successfully", "SUCCESS")
            return True
        else:
            log(f"Demo Request Failed: {resp.text}", "FAIL")
            return False
    except Exception as e:
        log(f"Demo Request Exception: {e}", "FAIL")
        return False

if __name__ == "__main__":
    if check_health() and check_frontend():
        if test_demo_request():
            log("✅ DEPLOYMENT VERIFICATION PASSED", "SUCCESS")
            sys.exit(0)
    
    log("❌ DEPLOYMENT VERIFICATION FAILED", "FAIL")
    sys.exit(1)
