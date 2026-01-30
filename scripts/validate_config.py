#!/usr/bin/env python3
"""
Configuration validation script.
Checks that all required environment variables are set for production deployment.
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from core.config import settings, validate_settings_runtime

def check_required_production():
    """Check required production settings"""
    print("🔍 Checking required production settings...")
    errors = []
    warnings = []
    
    # Critical security keys
    critical_keys = [
        "JWT_SECRET_KEY",
        "STORAGE_ENCRYPTION_KEY",
        "DOCS_ENCRYPTION_KEY",
    ]
    
    for key in critical_keys:
        value = getattr(settings, key, None)
        if not value or value in ["change-me", "dev-secret", "dev-storage", "dev-docs"]:
            errors.append(f"❌ {key}: Must be set to a strong random value (currently: {value[:20] if value else 'None'}...)")
        else:
            print(f"✅ {key}: Set")
    
    # Database
    if not settings.DATABASE_URL or "sqlite" in settings.DATABASE_URL:
        errors.append("❌ DATABASE_URL: Must be PostgreSQL connection string for production")
    else:
        print(f"✅ DATABASE_URL: Configured")
    
    # Allowed origins
    if not settings.ALLOWED_ORIGINS or "localhost" in settings.ALLOWED_ORIGINS:
        warnings.append("⚠️  ALLOWED_ORIGINS: Contains localhost - update for production")
    else:
        print(f"✅ ALLOWED_ORIGINS: Configured")
    
    return errors, warnings

def check_optional_services():
    """Check optional service configurations"""
    print("\n🔍 Checking optional service configurations...")
    warnings = []
    
    # Email
    if not settings.SMTP_PASSWORD:
        warnings.append("⚠️  SMTP_PASSWORD: Not set - email sending will fail")
    else:
        print("✅ SMTP_PASSWORD: Set")
    
    # Telnyx
    if settings.TELNYX_ENABLED and not settings.TELNYX_API_KEY:
        warnings.append("⚠️  TELNYX_API_KEY: Not set but TELNYX_ENABLED=true - SMS/phone will fail")
    elif settings.TELNYX_API_KEY:
        print("✅ TELNYX_API_KEY: Set")
    
    # Stripe
    if not settings.stripe_secret_key:
        warnings.append("⚠️  STRIPE_SECRET_KEY: Not set - payment processing disabled")
    else:
        print("✅ STRIPE_SECRET_KEY: Set")
    
    # Office Ally
    if settings.OFFICEALLY_ENABLED:
        if not settings.OFFICEALLY_FTP_PASSWORD:
            warnings.append("⚠️  OFFICEALLY_FTP_PASSWORD: Not set but OFFICEALLY_ENABLED=true")
        else:
            print("✅ Office Ally: Configured")
    
    # DigitalOcean Spaces
    if settings.SPACES_ACCESS_KEY and settings.SPACES_SECRET_KEY:
        print("✅ DigitalOcean Spaces: Configured")
    else:
        warnings.append("⚠️  DigitalOcean Spaces: Not configured - file storage will fail")
    
    return warnings

def main():
    """Main validation function"""
    print("=" * 60)
    print("FusionEMS Quantum - Configuration Validation")
    print("=" * 60)
    print(f"Environment: {settings.ENV}")
    print()
    
    # Check required production settings
    errors, warnings = check_required_production()
    
    # Check optional services
    optional_warnings = check_optional_services()
    warnings.extend(optional_warnings)
    
    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for error in errors:
            print(f"  {error}")
        print("\n⚠️  These must be fixed before production deployment!")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"  {warning}")
        print("\n💡 These should be configured for full functionality.")
    
    if not errors and not warnings:
        print("\n✅ All checks passed! Configuration looks good.")
    
    # Runtime validation
    print("\n" + "=" * 60)
    print("Runtime Validation")
    print("=" * 60)
    try:
        validate_settings_runtime()
        print("✅ Runtime validation passed")
    except RuntimeError as e:
        print(f"❌ Runtime validation failed: {e}")
        errors.append(str(e))
    
    # Exit code
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
