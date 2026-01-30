#!/usr/bin/env python3
"""
Extract Lob activation/verification link from email content.
Paste the email body/content here and it will find the activation link.
"""
import sys
import re
from urllib.parse import urlparse, parse_qs

def extract_activation_links(text):
    """Extract activation/verification links from email content"""
    if not text:
        return []
    
    # Pattern to match URLs
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:!?]'
    urls = re.findall(url_pattern, text)
    
    # Also look for HTML links
    html_link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>'
    html_links = re.findall(html_link_pattern, text, re.IGNORECASE)
    
    all_links = list(set(urls + html_links))
    
    # Clean links (remove trailing punctuation)
    cleaned_links = []
    for link in all_links:
        # Remove trailing punctuation that might have been included
        link = link.rstrip('.,;:!?)')
        cleaned_links.append(link)
    
    return cleaned_links

def find_activation_link(links):
    """Find the most relevant activation/verification link"""
    activation_links = []
    verification_links = []
    lob_dashboard_links = []
    
    for link in links:
        link_lower = link.lower()
        
        # Priority 1: Direct activation/verification links
        if any(keyword in link_lower for keyword in ['activate', 'activation', 'verify', 'verification', 'confirm', 'confirmation']):
            if 'lob' in link_lower:
                activation_links.append(link)
            else:
                verification_links.append(link)
        
        # Priority 2: Lob dashboard links with tokens/keys
        elif 'lob.com' in link_lower or 'dashboard.lob.com' in link_lower:
            if any(keyword in link_lower for keyword in ['token', 'key', 'verify', 'activate', 'confirm']):
                activation_links.append(link)
            else:
                lob_dashboard_links.append(link)
    
    return activation_links, verification_links, lob_dashboard_links

def main():
    print("="*70)
    print("Lob Activation Link Extractor")
    print("="*70)
    print()
    print("📧 Paste the email content below (the body/text of the Lob email)")
    print("   Press Ctrl+D when done, or type 'done' on a new line")
    print()
    print("-"*70)
    
    # Read email content
    lines = []
    try:
        while True:
            line = input()
            if line.lower().strip() == 'done':
                break
            lines.append(line)
    except EOFError:
        pass
    
    email_content = "\n".join(lines)
    
    if not email_content.strip():
        print()
        print("❌ No email content provided")
        print()
        print("Usage:")
        print("  1. Open the Lob email in your platform")
        print("  2. Copy the email body/content")
        print("  3. Run this script and paste the content")
        print("  4. Press Ctrl+D or type 'done'")
        print()
        print("Or provide as argument:")
        print("  python3 extract_lob_activation_link.py 'email content here'")
        return
    
    print()
    print("-"*70)
    print("🔍 Searching for activation links...")
    print("-"*70)
    print()
    
    # Extract all links
    all_links = extract_activation_links(email_content)
    
    if not all_links:
        print("❌ No links found in email content")
        print()
        print("💡 Make sure you copied the full email body, including HTML if available")
        return
    
    print(f"✅ Found {len(all_links)} link(s) in email")
    print()
    
    # Find activation links
    activation_links, verification_links, lob_dashboard_links = find_activation_link(all_links)
    
    # Display results
    print("="*70)
    print("🎯 ACTIVATION LINKS (Click these to activate your account)")
    print("="*70)
    print()
    
    if activation_links:
        for i, link in enumerate(activation_links, 1):
            print(f"{i}. {link}")
            print()
        print("✅ Use one of the links above to activate your Lob account!")
    elif verification_links:
        print("Found verification links (may also work for activation):")
        for i, link in enumerate(verification_links, 1):
            print(f"{i}. {link}")
            print()
    else:
        print("⚠️  No direct activation links found, but found Lob dashboard links:")
        print()
        if lob_dashboard_links:
            for i, link in enumerate(lob_dashboard_links, 1):
                print(f"{i}. {link}")
                print()
        else:
            print("Showing all links found:")
            print()
            for i, link in enumerate(all_links[:10], 1):
                print(f"{i}. {link}")
                print()
    
    # Show all links for reference
    if len(all_links) > len(activation_links) + len(verification_links) + len(lob_dashboard_links):
        print("="*70)
        print("🔗 All Links Found (for reference)")
        print("="*70)
        print()
        for i, link in enumerate(all_links, 1):
            if link not in activation_links and link not in verification_links and link not in lob_dashboard_links:
                print(f"{i}. {link}")
        print()
    
    # Instructions
    print("="*70)
    print("📝 Next Steps")
    print("="*70)
    print()
    print("1. Copy one of the activation links above")
    print("2. Open it in your web browser")
    print("3. Complete the activation/verification process")
    print("4. After activation, get your API key from:")
    print("   https://dashboard.lob.com/settings/api-keys")
    print("5. Add API key to .env:")
    print("   LOB_API_KEY=test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    print("   LOB_ENABLED=true")
    print()
    
    # If no activation link found, provide alternatives
    if not activation_links and not verification_links:
        print("="*70)
        print("💡 Alternative: Direct Activation")
        print("="*70)
        print()
        print("If no activation link was found, you can activate directly:")
        print()
        print("1. Go to: https://dashboard.lob.com")
        print("2. Sign up/Log in with: joshua.j.wendorf@fusionemsquantum.com")
        print("3. Complete account setup")
        print("4. Verify your email if prompted")
        print("5. Get API key from Settings → API Keys")
        print()

if __name__ == "__main__":
    # Allow email content as command line argument
    if len(sys.argv) > 1:
        email_content = " ".join(sys.argv[1:])
        # Temporarily override input
        import io
        sys.stdin = io.StringIO(email_content + "\ndone")
    
    main()
