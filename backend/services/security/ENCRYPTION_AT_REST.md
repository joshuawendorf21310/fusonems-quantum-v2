# Encryption at Rest (FedRAMP SC-28)

This module implements FedRAMP SC-28 (Protection of Information at Rest) using FIPS 140-2 compliant cryptographic modules.

## Overview

The encryption at rest implementation provides:
- **Database column encryption**: Transparent encryption/decryption of sensitive database fields
- **File encryption**: Encrypt files stored on disk
- **Key rotation support**: Automatic key rotation with backward compatibility
- **FIPS 140-2 compliance**: Uses validated cryptographic modules

## Components

### 1. EncryptionAtRestService
Core service for encrypting data at rest.

**Location**: `backend/services/security/encryption_at_rest.py`

**Features**:
- Database column encryption/decryption
- File encryption/decryption
- Key rotation support
- FIPS 140-2 compliance

**Usage**:
```python
from sqlalchemy.orm import Session
from services.security import EncryptionAtRestService

db: Session = get_db()
encryption_service = EncryptionAtRestService(db)

# Encrypt a column value
encrypted = encryption_service.encrypt_column_value("sensitive data")

# Decrypt a column value
decrypted = encryption_service.decrypt_column_value(encrypted)

# Encrypt a file
encrypted_file = encryption_service.encrypt_file(Path("data.txt"))

# Decrypt a file
decrypted_file = encryption_service.decrypt_file(encrypted_file)
```

### 2. DatabaseEncryptionService
Service for automatic field-level encryption in SQLAlchemy models.

**Location**: `backend/services/security/database_encryption_service.py`

**Features**:
- Automatic encryption on write
- Automatic decryption on read
- Field-level encryption
- Integration with key management

**Usage**:
```python
from sqlalchemy.orm import Session
from services.security import DatabaseEncryptionService
from models.epcr_core import Patient

db: Session = get_db()
encryption_service = DatabaseEncryptionService(db)

# Register encrypted fields for a model
encryption_service.register_encrypted_fields(
    Patient,
    ["first_name", "last_name", "date_of_birth", "phone"]
)

# Now all Patient instances will automatically encrypt/decrypt these fields
patient = Patient(first_name="John", last_name="Doe", ...)
db.add(patient)
db.commit()  # Fields are automatically encrypted before save

# When reading, fields are automatically decrypted
patient = db.query(Patient).first()
print(patient.first_name)  # Automatically decrypted
```

### 3. EncryptedString / EncryptedText
SQLAlchemy custom types for transparent encryption.

**Location**: `backend/utils/encrypted_field.py`

**Usage**:
```python
from sqlalchemy import Column, Integer
from utils.encrypted_field import EncryptedString
from core.database import Base

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True)
    ssn = Column(EncryptedString(255))  # Encrypted SSN
    email = Column(EncryptedString(255))  # Encrypted email
    notes = Column(EncryptedText())  # Encrypted text (unlimited length)
```

## Initialization

To enable encryption at rest for your models, initialize the encryption service:

```python
from sqlalchemy.orm import Session
from services.security.encryption_init import initialize_encryption

db: Session = get_db()
encryption_service = initialize_encryption(db)
```

This registers encrypted fields for:
- Patient model (PHI fields)
- TelehealthPatient model (PHI fields)
- User model (PII fields)
- Payment models (payment information)

## Key Management

Encryption keys are managed by `KeyManagementService`:
- Keys are automatically generated on first use
- Keys rotate every 90 days (configurable)
- Deprecated keys are retained for backward compatibility
- Keys are escrowed for recovery

## Backward Compatibility

The implementation supports backward compatibility:
- Existing unencrypted data continues to work
- New data is automatically encrypted
- Decryption gracefully handles both encrypted and unencrypted values
- Migration can be done gradually

## Migration Strategy

1. **Phase 1**: Deploy encryption infrastructure
   - Run migration to create encryption_metadata table
   - Initialize encryption service
   - Existing data remains unencrypted

2. **Phase 2**: Enable encryption for new data
   - Register encrypted fields
   - New writes are automatically encrypted
   - Reads handle both encrypted and unencrypted

3. **Phase 3**: Migrate existing data (optional)
   - Bulk encrypt existing records
   - Update encryption_metadata status

## Configuration

Required environment variables:
- `KEY_MANAGEMENT_MASTER_KEY`: Master key for encrypting stored keys (32+ bytes)
- `FIPS_MODE_ENABLED`: Enable FIPS mode (optional, defaults to false)

## Security Considerations

1. **Key Storage**: Keys are encrypted with a master key before storage
2. **Key Rotation**: Keys rotate automatically; deprecated keys are retained
3. **FIPS Compliance**: Uses FIPS 140-2 validated cryptographic modules
4. **Access Control**: Encryption keys are protected by key management service
5. **Audit**: All encryption operations can be audited via audit logs

## Compliance

This implementation satisfies:
- **FedRAMP SC-28**: Protection of Information at Rest
- **FedRAMP SC-13**: Use FIPS 140-2 validated cryptographic modules
- **FedRAMP SC-12**: Cryptographic key establishment and management

## Troubleshooting

### Encryption fails
- Check that `KEY_MANAGEMENT_MASTER_KEY` is set
- Verify FIPS mode if required
- Check logs for specific error messages

### Decryption fails
- Verify key is not revoked
- Check if deprecated keys are available for rotation
- Ensure associated_data matches encryption

### Performance impact
- Encryption/decryption adds minimal overhead
- Keys are cached for performance
- File encryption uses chunked processing

## Examples

See `backend/services/security/encryption_init.py` for examples of registering encrypted fields.
