# FIPS 140-2 Compliance Implementation

This directory contains FIPS 140-2 compliant cryptographic services for FedRAMP SC-13 compliance.

## Overview

The implementation provides:
- **FIPS-compliant cryptographic operations** (`core/crypto.py`)
- **Key management service** with lifecycle management (`key_management_service.py`)
- **FIPS validation utilities** (`utils/fips_validator.py`)
- **FIPS-aware password hashing** (updated `core/security.py`)

## Configuration

Add to your `.env` file:

```bash
# FIPS 140-2 Compliance
FIPS_MODE_ENABLED=false  # Set to true to enable FIPS mode
FIPS_MODE_REQUIRED=false  # Set to true to require FIPS (fails startup if unavailable)

# Password Policy (FedRAMP IA-5)
PASSWORD_MIN_LENGTH=14
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_DIGITS=true
PASSWORD_REQUIRE_SPECIAL=true
PASSWORD_MAX_AGE_DAYS=90

# Password Hashing
PASSWORD_HASH_ALGORITHM=auto  # auto, bcrypt, pbkdf2, argon2
PBKDF2_ITERATIONS=100000  # Minimum recommended: 100000

# Key Management (FedRAMP SC-12)
KEY_MANAGEMENT_MASTER_KEY=your-32-byte-master-key-here
KEY_ESCROW_LOCATION=/secure/escrow/location
KEY_ROTATION_INTERVAL_DAYS=90
```

## Usage

### Cryptographic Operations

```python
from core.crypto import (
    encrypt_aes256_gcm_base64,
    decrypt_aes256_gcm_base64,
    hash_sha256,
    hmac_sha256,
    derive_key_pbkdf2,
    is_fips_enabled
)

# Check FIPS status
if is_fips_enabled():
    print("FIPS mode is enabled")

# Encrypt data
key = generate_key(32)  # 32 bytes for AES-256
encrypted = encrypt_aes256_gcm_base64("sensitive data", key)
decrypted = decrypt_aes256_gcm_base64(encrypted, key)

# Hash data
hash_value = hash_sha256(b"data to hash")

# HMAC
hmac_value = hmac_sha256(key, b"data to authenticate")

# Key derivation
derived_key = derive_key_pbkdf2(
    password=b"password",
    salt=get_random_bytes(16),
    iterations=100000,
    key_length=32
)
```

### Key Management

```python
from services.security.key_management_service import (
    KeyManagementService,
    KeyType,
    KeyStatus
)
from core.database import get_db

# Initialize service
db = next(get_db())
key_service = KeyManagementService(db)

# Generate a new key
key_id = key_service.generate_key(
    key_type=KeyType.ENCRYPTION,
    rotation_interval_days=90,
    escrow=True
)

# Retrieve key
key_material = key_service.get_key(key_id)

# Rotate key
new_key_id = key_service.rotate_key(key_id)

# List keys
active_keys = key_service.list_keys(status=KeyStatus.ACTIVE)

# Auto-rotate expired keys
rotated = key_service.auto_rotate_expired_keys()
```

### Password Hashing

```python
from core.security import hash_password, verify_password, validate_password_complexity

# Validate password complexity
is_valid, error = validate_password_complexity("MySecureP@ssw0rd")
if not is_valid:
    print(f"Password error: {error}")

# Hash password (automatically uses PBKDF2 if FIPS enabled)
hashed = hash_password("MySecureP@ssw0rd")

# Verify password
is_correct = verify_password("MySecureP@ssw0rd", hashed)
```

### FIPS Validation

```python
from utils.fips_validator import validate_fips_compliance, log_fips_status

# Validate FIPS compliance
summary = validate_fips_compliance()
print(f"FIPS Status: {summary['overall_status']}")
print(f"Checks Passed: {summary['checks_passed']}/{summary['total_checks']}")

# Log validation results
log_fips_status()
```

## FIPS Mode Detection

The system automatically detects FIPS mode through:
1. `/proc/sys/crypto/fips_enabled` (Linux)
2. `FIPS_MODE` environment variable
3. `FIPS_MODE_ENABLED` setting

## Graceful Fallback

When FIPS modules are not available:
- Cryptographic operations fall back to standard libraries
- Password hashing uses bcrypt (backward compatible)
- System continues to operate with warnings logged

## Database Migration

Run the migration to create the encryption_keys table:

```bash
alembic upgrade head
```

## Security Notes

1. **Master Key**: Set `KEY_MANAGEMENT_MASTER_KEY` to a strong 32-byte value in production
2. **Key Escrow**: Configure `KEY_ESCROW_LOCATION` for key recovery
3. **FIPS Mode**: Enable system-level FIPS mode for full compliance
4. **Password Policy**: Adjust complexity requirements per your security policy

## FedRAMP Compliance

This implementation addresses:
- **SC-12**: Cryptographic key establishment and management
- **SC-13**: Use of FIPS 140-2 validated cryptographic modules
- **IA-5**: Password-based authentication (complexity requirements)
