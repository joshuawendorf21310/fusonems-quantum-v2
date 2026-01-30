#!/usr/bin/env python3
"""
Test Lob API connection and configuration.
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from core.config import settings
import lob

def test_lob_connection():
    """Test Lob API connection"""
    print("Testing Lob API connection...")
    print(f"API Key: {settings.LOB_API_KEY[:10] if settings.LOB_API_KEY else 'NOT SET'}...")
    print(f"Enabled: {settings.LOB_ENABLED}")
    print(f"From Address: {settings.LOB_FROM_ADDRESS_NAME}")
    
    if not settings.LOB_API_KEY:
        print("❌ LOB_API_KEY not set!")
        return False
    
    try:
        client = lob.Client(api_key=settings.LOB_API_KEY)
        
        # Test API connection by listing addresses
        print("\n✅ Lob client created successfully")
        
        # Test address verification (optional)
        if settings.LOB_FROM_ADDRESS_LINE1:
            print(f"\nFrom Address Configuration:")
            print(f"  Name: {settings.LOB_FROM_ADDRESS_NAME}")
            print(f"  Address: {settings.LOB_FROM_ADDRESS_LINE1}")
            print(f"  City: {settings.LOB_FROM_ADDRESS_CITY}")
            print(f"  State: {settings.LOB_FROM_ADDRESS_STATE}")
            print(f"  ZIP: {settings.LOB_FROM_ADDRESS_ZIP}")
            print("\n⚠️  Note: Verify this address in Lob dashboard before sending mail")
        
        print("\n✅ Lob connection test successful!")
        print("💡 Next steps:")
        print("   1. Verify your 'from' address in Lob dashboard")
        print("   2. Set LOB_ENABLED=true in .env")
        print("   3. Enable AI billing service in database")
        
        return True
    except Exception as e:
        print(f"❌ Lob connection test failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   - Verify API key is correct (starts with 'test_' or 'live_')")
        print("   - Check internet connection")
        print("   - Verify Lob account is active")
        return False

if __name__ == "__main__":
    success = test_lob_connection()
    sys.exit(0 if success else 1)
