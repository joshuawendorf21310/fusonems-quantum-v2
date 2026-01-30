#!/usr/bin/env python3
"""
Test Office Ally SFTP connection.
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from core.config import settings
import paramiko

def test_sftp():
    """Test SFTP connection to Office Ally"""
    print("Testing Office Ally SFTP connection...")
    print(f"Host: {settings.OFFICEALLY_FTP_HOST}")
    print(f"Port: {settings.OFFICEALLY_FTP_PORT}")
    print(f"Username: {settings.OFFICEALLY_FTP_USER}")
    print(f"Directory: {settings.OFFICEALLY_SFTP_DIRECTORY}")
    
    if not settings.OFFICEALLY_FTP_PASSWORD:
        print("❌ OFFICEALLY_FTP_PASSWORD not set!")
        return False
    
    try:
        transport = paramiko.Transport((settings.OFFICEALLY_FTP_HOST, settings.OFFICEALLY_FTP_PORT))
        transport.connect(username=settings.OFFICEALLY_FTP_USER, password=settings.OFFICEALLY_FTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        # Test listing directory
        try:
            files = sftp.listdir(settings.OFFICEALLY_SFTP_DIRECTORY)
            print(f"✅ Connected successfully!")
            print(f"✅ Found {len(files)} files in {settings.OFFICEALLY_SFTP_DIRECTORY}/")
            if files:
                print(f"   Sample files: {files[:5]}")
        except IOError as e:
            print(f"⚠️  Directory {settings.OFFICEALLY_SFTP_DIRECTORY} may not exist: {e}")
            print("   This is normal if it's a new account.")
        
        sftp.close()
        transport.close()
        
        print("✅ SFTP connection test successful!")
        return True
    except Exception as e:
        print(f"❌ SFTP connection test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_sftp()
    sys.exit(0 if success else 1)
