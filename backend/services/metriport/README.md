# Metriport Integration — Patient Information

**We use Metriport for patient information.** This integration provides demographics, insurance verification, and medical history via the Metriport API (no generic EHR/HL7 build from scratch).

## Features

### Patient Demographics
- **Patient Creation**: Create patients in Metriport HIE network
- **Patient Search**: Search across health information exchanges
- **Patient Matching**: Automatic deduplication and matching logic
- **Master Patient Index**: Link local patients to Metriport patients

### Insurance Verification
- **Real-time Eligibility**: Check insurance eligibility in real-time
- **Coverage Details**: Retrieve copay, deductible, and coverage information
- **Multi-Coverage Support**: Primary, secondary, and tertiary insurance
- **Verification History**: Complete audit log of all verifications
- **Manual Retry**: Retry failed verifications

### Medical History Access
- **FHIR Documents**: Access C-CDA and consolidated documents
- **Document Sync**: Automatic document synchronization
- **Medical Data Parsing**: Parse FHIR bundles for allergies, medications, conditions
- **Document Management**: Track and store medical documents

### Webhook Integration
- **Real-time Updates**: Process Metriport webhooks for events
- **Document Ready**: Notifications when documents are ready
- **Patient Discovery**: Updates on patient discovery in HIEs
- **Consolidated Data**: Notifications for consolidated data availability

## Architecture

```
backend/
├── models/
│   └── metriport.py                    # Database models
├── services/
│   └── metriport/
│       ├── metriport_service.py        # Core service logic
│       ├── metriport_router.py         # API endpoints
│       └── metriport_webhooks.py       # Webhook handlers
└── alembic/
    └── versions/
        └── 20260127_metriport_integration.py  # Database migration

frontend/
└── src/
    └── components/
        └── metriport/
            ├── InsuranceVerificationStatus.tsx
            ├── VerifyInsuranceForm.tsx
            ├── MedicalHistoryDocuments.tsx
            └── InsuranceVerificationDashboard.tsx
```

## Database Models

### PatientInsurance
Stores insurance information and verification status for patients.

**Key Fields:**
- `payer_name`, `member_id`, `coverage_type`
- `verification_status`: pending, verified, failed, manual_review, expired
- `is_active`: coverage active status
- `copay_amount`, `deductible_amount`
- `raw_eligibility_response`: full API response

### MetriportPatientMapping
Maps local patients to Metriport patient IDs.

**Key Fields:**
- `metriport_patient_id`: Unique Metriport identifier
- `master_patient_id`, `epcr_patient_id`: Local patient references
- `sync_status`: pending, in_progress, completed, failed
- `mapping_verified`: manual verification flag

### MetriportWebhookEvent
Logs all webhook events from Metriport.

**Event Types:**
- `medical.document-download`
- `medical.document-conversion`
- `medical.consolidated-data`
- `medical.patient-discovery`

### MetriportDocumentSync
Tracks medical document synchronization.

**Key Fields:**
- `document_id`, `document_type`, `document_title`
- `fhir_bundle`: Raw FHIR data
- `parsed_data`: Extracted medical information
- `sync_status`: download and parsing status

### InsuranceVerificationLog
Audit log for all insurance verification attempts.

**Key Fields:**
- `verification_type`, `verification_status`
- `request_payload`, `response_payload`
- `is_eligible`, `eligibility_message`
- `duration_ms`: response time tracking

## API Endpoints

### Patient Management
```
POST   /api/metriport/patient/create       # Create patient in Metriport
POST   /api/metriport/patient/search       # Search for patients
```

### Insurance Verification
```
POST   /api/metriport/insurance/verify     # Verify insurance eligibility
GET    /api/metriport/insurance/{id}       # Get insurance records
POST   /api/metriport/insurance/{id}/retry # Retry failed verification
GET    /api/metriport/verification-log/{id} # Get verification history
```

### Document Management
```
POST   /api/metriport/documents/sync       # Sync medical documents
GET    /api/metriport/documents/{id}       # Get synced documents
GET    /api/metriport/consolidated/{id}    # Get consolidated FHIR data
```

### Webhooks
```
POST   /api/metriport/webhooks/events      # Webhook receiver
GET    /api/metriport/webhooks/events/pending  # Get pending events
POST   /api/metriport/webhooks/events/{id}/retry  # Retry event processing
GET    /api/metriport/webhooks/events/stats  # Webhook statistics
```

## Configuration

Add to `.env`:

```bash
# Metriport Configuration
METRIPORT_ENABLED=true
METRIPORT_API_KEY=your_api_key_here
METRIPORT_BASE_URL=https://api.metriport.com/medical/v1
METRIPORT_FACILITY_ID=your_facility_id
METRIPORT_WEBHOOK_SECRET=your_webhook_secret
```

## Usage Examples

### 1. Create Patient and Verify Insurance

```python
from services.metriport.metriport_service import get_metriport_service

service = get_metriport_service()

# Create patient
metriport_patient_id = await service.create_patient(
    db=db,
    org_id=1,
    first_name="John",
    last_name="Doe",
    date_of_birth="1990-01-01",
    gender="M",
    master_patient_id=123
)

# Verify insurance
verification = await service.verify_insurance(
    db=db,
    org_id=1,
    metriport_patient_id=metriport_patient_id,
    payer_id="00001",
    member_id="ABC123456",
    master_patient_id=123
)

# Store results
insurance = service.store_insurance_verification(
    db=db,
    org_id=1,
    master_patient_id=123,
    verification_data=verification
)
```

### 2. Frontend Components

```typescript
import {
  InsuranceVerificationStatus,
  VerifyInsuranceForm,
  MedicalHistoryDocuments
} from '@/components/metriport';

function PatientInsuranceTab({ patientId }) {
  return (
    <div className="space-y-6">
      {/* Display current insurance status */}
      <InsuranceVerificationStatus
        patientId={patientId}
        patientType="master"
        onVerificationComplete={() => console.log('Verification updated')}
      />

      {/* Form to verify new insurance */}
      <VerifyInsuranceForm
        patientId={patientId}
        patientType="master"
        onVerificationComplete={() => console.log('Verification complete')}
      />

      {/* Display synced medical documents */}
      <MedicalHistoryDocuments
        patientId={patientId}
        patientType="master"
      />
    </div>
  );
}
```

### 3. Webhook Handler

Webhooks are automatically processed when Metriport sends events:

```python
# Automatically handled by metriport_webhooks.py

# Event types:
# - medical.document-download: Document ready for download
# - medical.document-conversion: Document converted to FHIR
# - medical.consolidated-data: Consolidated data ready
# - medical.patient-discovery: Patient found in HIEs
```

## Security & Compliance

### PHI Protection
- All patient data marked with `classification="PHI"`
- Training mode flag for test data
- Encryption at rest for sensitive fields

### Audit Logging
- Complete verification history in `InsuranceVerificationLog`
- Webhook event tracking
- Document access logging

### CSRF Protection
- Webhook endpoints exempted from CSRF checks
- Signature verification for webhooks (implement based on Metriport docs)

## Error Handling

### Verification Failures
- Failed verifications stored with error messages
- Manual retry available via API
- Automatic retry logic for transient failures

### Webhook Processing
- Failed webhooks logged with error details
- Retry counter with max attempts (5)
- Admin interface for manual reprocessing

## Monitoring

### Admin Dashboard
The `InsuranceVerificationDashboard` component provides:
- Total verification count
- Success/failure rates
- Average response times
- Recent verification activity
- Status breakdown

### Metrics to Track
- Verification success rate
- Average verification time
- Failed verification reasons
- Document sync completion rate
- Webhook processing success rate

## Testing

### Manual Testing
1. Enable Metriport in configuration
2. Create test patient
3. Use VerifyInsuranceForm component
4. Check verification status
5. Sync medical documents
6. Monitor webhook events

### Integration Testing
```python
# Example test
async def test_insurance_verification():
    service = get_metriport_service()
    
    result = await service.verify_insurance(
        db=test_db,
        org_id=1,
        metriport_patient_id="test_patient_id",
        payer_id="00001",
        member_id="TEST123"
    )
    
    assert result is not None
    assert 'eligible' in result
```

## Deployment Checklist

- [ ] Add Metriport API credentials to environment
- [ ] Run database migration: `alembic upgrade head`
- [ ] Configure webhook URL in Metriport dashboard
- [ ] Test insurance verification flow
- [ ] Verify webhook processing
- [ ] Set up monitoring and alerting
- [ ] Train staff on verification interface

## Troubleshooting

### Common Issues

**Issue: Verification fails with "Patient not found"**
- Solution: Create patient in Metriport first using `/api/metriport/patient/create`

**Issue: Webhooks not being processed**
- Check webhook secret configuration
- Verify webhook URL is accessible from Metriport
- Check `metriport_webhook_events` table for errors

**Issue: Documents not syncing**
- Verify patient mapping exists
- Check `metriport_document_sync` table for sync status
- Manually trigger sync via API

## Support

For Metriport API support:
- Documentation: https://docs.metriport.com
- Support: support@metriport.com

For integration issues:
- Check logs in `utils/logger.py`
- Review webhook event logs
- Contact development team
