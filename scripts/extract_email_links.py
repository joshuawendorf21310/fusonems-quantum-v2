#!/usr/bin/env python3
"""
Extract links from email content (paste email body here or provide as argument).
"""
import sys
import re
from urllib.parse import urlparse

def extract_links(text):
    """Extract all URLs from text"""
    # Pattern to match URLs
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:!?]'
    urls = re.findall(url_pattern, text)
    
    # Also look for common email link patterns
    email_link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>'
    email_links = re.findall(email_link_pattern, text, re.IGNORECASE)
    
    all_links = list(set(urls + email_links))
    return all_links

def categorize_link(url):
    """Categorize Lob-related links"""
    url_lower = url.lower()
    
    if 'dashboard.lob.com' in url_lower or 'lob.com/dashboard' in url_lower:
        return "🔗 Lob Dashboard"
    elif 'api.lob.com' in url_lower:
        return "🔗 Lob API Documentation"
    elif 'verify' in url_lower or 'verification' in url_lower:
        return "✅ Verification Link"
    elif 'api-keys' in url_lower or 'apikey' in url_lower or 'api_key' in url_lower:
        return "🔑 API Key Page"
    elif 'settings' in url_lower:
        return "⚙️ Settings Page"
    elif 'docs.lob.com' in url_lower:
        return "📚 Documentation"
    elif 'support' in url_lower or 'help' in url_lower:
        return "🆘 Support/Help"
    else:
        return "🔗 Other Link"

def main():
    print("="*60)
    print("Email Link Extractor - Looking for Lob Links")
    print("="*60)
    print()
    
    # Get email content
    if len(sys.argv) > 1:
        # Email content provided as argument
        email_content = " ".join(sys.argv[1:])
    else:
        # Read from stdin or prompt
        print("Paste the email content below (press Ctrl+D when done, or type 'done'):")
        print()
        lines = []
        try:
            while True:
                line = input()
                if line.lower() == 'done':
                    break
                lines.append(line)
        except EOFError:
            pass
        email_content = "\n".join(lines)
    
    if not email_content.strip():
        print("❌ No email content provided")
        print("\nUsage:")
        print("  python3 extract_email_links.py 'email content here'")
        print("  OR")
        print("  python3 extract_email_links.py")
        print("  (then paste email content)")
        return
    
    # Extract links
    links = extract_links(email_content)
    
    if not links:
        print("❌ No links found in email content")
        return
    
    print(f"✅ Found {len(links)} link(s):\n")
    
    # Categorize and display
    lob_links = []
    other_links = []
    
    for link in links:
        category = categorize_link(link)
        if 'lob' in link.lower() or 'verify' in link.lower():
            lob_links.append((category, link))
        else:
            other_links.append((category, link))
    
    # Show Lob-related links first
    if lob_links:
        print("🎯 Lob-Related Links:")
        print("-" * 60)
        for category, link in lob_links:
            print(f"{category}: {link}")
        print()
    
    # Show other links
    if other_links:
        print("🔗 Other Links:")
        print("-" * 60)
        for category, link in other_links:
            print(f"{category}: {link}")
        print()
    
    # Most important links
    print("="*60)
    print("📋 Most Important Links:")
    print("="*60)
    
    # Look for specific important links
    dashboard_links = [l for _, l in lob_links if 'dashboard' in l.lower()]
    verify_links = [l for _, l in lob_links if 'verify' in l.lower()]
    api_key_links = [l for _, l in lob_links if 'api' in l.lower() and 'key' in l.lower()]
    
    if dashboard_links:
        print(f"\n🔗 Lob Dashboard: {dashboard_links[0]}")
    if verify_links:
        print(f"\n✅ Verification Link: {verify_links[0]}")
    if api_key_links:
        print(f"\n🔑 API Key Page: {api_key_links[0]}")
    
    # Default Lob links
    print("\n" + "="*60)
    print("🔗 Common Lob Links (if not found in email):")
    print("="*60)
    print("Dashboard: https://dashboard.lob.com")
    print("API Keys: https://dashboard.lob.com/settings/api-keys")
    print("Documentation: https://docs.lob.com")
    print("Support: https://support.lob.com")

if __name__ == "__main__":
    main()
