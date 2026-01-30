#!/usr/bin/env python3
"""
Test email configuration.
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from core.config import settings
import smtplib
from email.mime.text import MIMEText

def test_smtp():
    """Test SMTP connection"""
    print("Testing SMTP configuration...")
    print(f"Host: {settings.SMTP_HOST}")
    print(f"Port: {settings.SMTP_PORT}")
    print(f"Username: {settings.SMTP_USERNAME}")
    print(f"TLS: {settings.SMTP_USE_TLS}")
    
    if not settings.SMTP_PASSWORD:
        print("❌ SMTP_PASSWORD not set!")
        return False
    
    try:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        if settings.SMTP_USE_TLS:
            server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        
        # Send test email
        msg = MIMEText("This is a test email from FusionEMS Quantum configuration test.")
        msg['Subject'] = 'FusionEMS Quantum - Configuration Test'
        msg['From'] = settings.SMTP_USERNAME
        msg['To'] = settings.FOUNDER_EMAIL
        
        server.send_message(msg)
        server.quit()
        
        print("✅ SMTP test successful! Check inbox for test email.")
        return True
    except Exception as e:
        print(f"❌ SMTP test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_smtp()
    sys.exit(0 if success else 1)
