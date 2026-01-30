#!/usr/bin/env python3
"""
Check email inbox for Lob-related emails.
Note: This requires IMAP server to be accessible from this environment.
If it's not accessible, check your email directly or use the platform's email polling API.
"""
import sys
import imaplib
import email
import os
from email.header import decode_header
from pathlib import Path

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

def decode_mime_words(s):
    """Decode MIME encoded words"""
    if not s:
        return ""
    decoded_parts = decode_header(s)
    decoded_str = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            decoded_str += part.decode(encoding or 'utf-8', errors='ignore')
        else:
            decoded_str += part
    return decoded_str

def check_lob_emails():
    """Check IMAP inbox for Lob-related emails"""
    print("="*60)
    print("Checking email inbox for Lob emails...")
    print("="*60)
    
    # Load environment variables
    env = load_env()
    
    imap_host = env.get('IMAP_HOST', '')
    imap_port = int(env.get('IMAP_PORT', '993'))
    imap_username = env.get('IMAP_USERNAME', '')
    imap_password = env.get('IMAP_PASSWORD', '')
    imap_use_tls = env.get('IMAP_USE_TLS', 'true').lower() == 'true'
    
    print(f"\nIMAP Configuration:")
    print(f"  Host: {imap_host}")
    print(f"  Port: {imap_port}")
    print(f"  Username: {imap_username}")
    print(f"  Use TLS: {imap_use_tls}\n")
    
    if not imap_host or not imap_username or not imap_password:
        print("❌ IMAP settings not configured!")
        print("   Please set IMAP_HOST, IMAP_USERNAME, and IMAP_PASSWORD in .env")
        return False
    
    try:
        # Connect to IMAP server
        print("Connecting to IMAP server...")
        if imap_use_tls:
            mail = imaplib.IMAP4_SSL(imap_host, imap_port, timeout=10)
        else:
            mail = imaplib.IMAP4(imap_host, imap_port, timeout=10)
        
        print("✅ Connected to IMAP server")
        
        # Login
        print("Logging in...")
        mail.login(imap_username, imap_password)
        print("✅ Logged in successfully")
        
        # Select INBOX
        mail.select("INBOX")
        
        # Search for emails from Lob
        print("\n🔍 Searching for emails from Lob...")
        
        # Search for emails containing "lob" in subject or from address
        typ, data = mail.search(None, '(OR FROM "lob.com" FROM "lob.io" FROM "noreply@lob.com" FROM "support@lob.com" SUBJECT "lob" SUBJECT "Lob" SUBJECT "LOB" SUBJECT "verify" SUBJECT "Verify" SUBJECT "verification")')
        
        if not data or not data[0]:
            print("❌ No Lob emails found in search")
            
            # Check for any recent emails
            print("\n🔍 Checking for recent unread emails...")
            typ, data = mail.search(None, 'UNSEEN')
            if data and data[0]:
                unread_ids = data[0].split()
                print(f"Found {len(unread_ids)} unread email(s):")
                for num in unread_ids[:10]:
                    typ, msg_data = mail.fetch(num, '(RFC822)')
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            subject = decode_mime_words(msg.get("Subject", ""))
                            from_addr = decode_mime_words(msg.get("From", ""))
                            print(f"  - {subject} (from {from_addr})")
            else:
                print("No unread emails found")
            
            mail.logout()
            print("\n💡 Tip: Check your email directly or use the platform's email polling API")
            return False
        
        email_ids = data[0].split()
        print(f"✅ Found {len(email_ids)} Lob-related email(s)\n")
        
        # Fetch and display emails
        for i, num in enumerate(email_ids, 1):
            typ, msg_data = mail.fetch(num, '(RFC822)')
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Get email details
                    subject = decode_mime_words(msg.get("Subject", ""))
                    from_addr = decode_mime_words(msg.get("From", ""))
                    to_addr = decode_mime_words(msg.get("To", ""))
                    date_str = msg.get("Date", "")
                    
                    # Get body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type == "text/plain":
                                try:
                                    body = part.get_payload(decode=True).decode(errors="ignore")
                                except:
                                    pass
                                break
                            elif content_type == "text/html" and not body:
                                try:
                                    body = part.get_payload(decode=True).decode(errors="ignore")
                                except:
                                    pass
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode(errors="ignore")
                        except:
                            body = str(msg.get_payload())
                    
                    print(f"{'='*60}")
                    print(f"Email #{i}")
                    print(f"{'='*60}")
                    print(f"From: {from_addr}")
                    print(f"To: {to_addr}")
                    print(f"Subject: {subject}")
                    print(f"Date: {date_str}")
                    print(f"\nBody Preview:")
                    print(body[:1000] + ("..." if len(body) > 1000 else ""))
                    print()
        
        # Also check for recent unread emails
        print("\n🔍 Checking for recent unread emails...")
        typ, data = mail.search(None, 'UNSEEN')
        if data and data[0]:
            unread_count = len(data[0].split())
            print(f"✅ Found {unread_count} unread email(s)")
        
        mail.logout()
        print("\n✅ Email check complete!")
        return True
        
    except socket.gaierror as e:
        print(f"❌ Cannot resolve IMAP host '{imap_host}'")
        print(f"   Error: {e}")
        print("\n💡 This usually means:")
        print("   - The mail server is not accessible from this environment")
        print("   - DNS is not resolving the hostname")
        print("   - The server is behind a firewall")
        print("\n📧 Alternative: Check your email directly at:")
        print(f"   - Webmail: https://{imap_host.replace('mail.', '')}")
        print(f"   - Or use your email client")
        print("\n📚 See CHECK_LOB_EMAIL.md for more options")
        return False
    except Exception as e:
        print(f"❌ Error checking email: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 If IMAP is not accessible, check your email directly")
        print("   See CHECK_LOB_EMAIL.md for instructions")
        return False

if __name__ == "__main__":
    import socket
    success = check_lob_emails()
    sys.exit(0 if success else 1)
