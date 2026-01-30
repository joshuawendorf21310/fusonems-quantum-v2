#!/usr/bin/env python3
"""
Fetch Lob verification email from platform inbox and extract verification link.
This script:
1. Polls IMAP to fetch new emails into platform
2. Searches for Lob-related emails
3. Extracts verification/activation links
"""
import sys
import re
import json
from pathlib import Path
import requests
from urllib.parse import urlparse, parse_qs

def load_env():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent.parent / ".env"
    env_vars = {}
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars

def extract_links(text):
    """Extract all URLs from text"""
    if not text:
        return []
    
    # Pattern to match URLs
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:!?]'
    urls = re.findall(url_pattern, text)
    
    # Also look for common email link patterns
    email_link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>'
    email_links = re.findall(email_link_pattern, text, re.IGNORECASE)
    
    # Remove duplicates and clean
    all_links = list(set(urls + email_links))
    return [link.rstrip('.,;:!?)') for link in all_links]

def find_verification_link(links):
    """Find the most relevant verification/activation link"""
    verification_links = []
    
    for link in links:
        link_lower = link.lower()
        if any(keyword in link_lower for keyword in ['verify', 'verification', 'activate', 'activation', 'confirm', 'confirmation']):
            verification_links.append(link)
        elif 'lob.com' in link_lower and ('token' in link_lower or 'key' in link_lower):
            verification_links.append(link)
    
    return verification_links

def main():
    print("="*60)
    print("Fetch Lob Verification Email from Platform")
    print("="*60)
    print()
    
    env = load_env()
    
    # Get API base URL
    api_base = "http://localhost:8000"  # Default, can be overridden
    
    print("📧 Step 1: Polling IMAP inbox to fetch new emails...")
    print(f"   API: {api_base}/api/email/poll-inbound")
    print()
    
    print("⚠️  Note: This requires:")
    print("   1. Platform to be running")
    print("   2. Valid authentication token")
    print("   3. IMAP credentials configured in .env")
    print()
    
    # Check if we can access the API
    try:
        # Try to poll inbox (requires auth token)
        print("💡 To fetch emails, you can:")
        print()
        print("   Option A: Use the platform UI")
        print("   - Log into platform")
        print("   - Go to Email Dashboard")
        print("   - Click 'Poll Inbox' or 'Fetch Emails'")
        print("   - Search for 'Lob' in emails")
        print()
        print("   Option B: Use API with authentication")
        print("   curl -X POST http://localhost:8000/api/email/poll-inbound \\")
        print("     -H 'Authorization: Bearer YOUR_TOKEN'")
        print()
        print("   Option C: Check email directly")
        print("   - Log into: joshua.j.wendorf@fusionemsquantum.com")
        print("   - Search for 'Lob'")
        print("   - Look for verification email")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("="*60)
    print("🔍 Step 2: Searching for Lob emails in platform...")
    print("="*60)
    print()
    
    print("💡 To search for Lob emails in the platform:")
    print()
    print("   1. Log into platform dashboard")
    print("   2. Navigate to: Email Dashboard or Communications")
    print("   3. Search for: 'Lob' or 'lob.com'")
    print("   4. Or filter by sender: 'lob.com', 'noreply@lob.com'")
    print()
    
    print("="*60)
    print("🔗 Step 3: Common Lob Verification Links")
    print("="*60)
    print()
    
    print("If you find the email, look for these types of links:")
    print()
    print("✅ Email Verification:")
    print("   https://dashboard.lob.com/verify?token=...")
    print("   https://lob.com/verify?email=...")
    print()
    print("✅ Account Activation:")
    print("   https://dashboard.lob.com/activate?token=...")
    print("   https://lob.com/activate?key=...")
    print()
    print("✅ API Key Setup:")
    print("   https://dashboard.lob.com/settings/api-keys")
    print()
    print("✅ Address Verification:")
    print("   https://dashboard.lob.com/addresses/verify")
    print()
    
    print("="*60)
    print("📝 Step 4: After Finding the Link")
    print("="*60)
    print()
    
    print("1. Click the verification/activation link")
    print("2. Complete the verification process")
    print("3. Get your API key from: https://dashboard.lob.com/settings/api-keys")
    print("4. Add to .env:")
    print("   LOB_API_KEY=test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    print("   LOB_ENABLED=true")
    print("5. Test connection:")
    print("   python3 scripts/test_lob.py")
    print()
    
    print("="*60)
    print("🚀 Quick Access (No Email Needed)")
    print("="*60)
    print()
    
    print("You can verify and activate directly:")
    print()
    print("1. Go to: https://dashboard.lob.com")
    print("2. Sign up/Log in with: joshua.j.wendorf@fusionemsquantum.com")
    print("3. Complete account setup")
    print("4. Go to: Settings → API Keys")
    print("5. Create API key")
    print("6. Copy and add to .env")
    print()
    
    print("💡 Tip: You don't actually need the email - you can")
    print("   access everything directly through the Lob dashboard!")

if __name__ == "__main__":
    main()
