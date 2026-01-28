CREATE TABLE IF NOT EXISTS billing_invoice_items (
    id VARCHAR PRIMARY KEY,
    org_id VARCHAR NOT NULL,
    invoice_id VARCHAR NOT NULL,
    description VARCHAR NOT NULL,
    code VARCHAR DEFAULT '',
    quantity INTEGER DEFAULT 1,
    unit_price INTEGER DEFAULT 0,
    amount INTEGER DEFAULT 0,
    metadata JSON DEFAULT '{}',
    classification VARCHAR DEFAULT 'BILLING_SENSITIVE',
    training_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS billing_invoice_events (
    id VARCHAR PRIMARY KEY,
    org_id VARCHAR NOT NULL,
    invoice_id VARCHAR NOT NULL,
    event_type VARCHAR NOT NULL,
    from_status VARCHAR DEFAULT '',
    to_status VARCHAR NOT NULL,
    payload JSON DEFAULT '{}',
    classification VARCHAR DEFAULT 'BILLING_SENSITIVE',
    training_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS billing_claims (
    id VARCHAR PRIMARY KEY,
    org_id VARCHAR NOT NULL,
    invoice_id VARCHAR NOT NULL,
    payer VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'draft',
    submission_reference VARCHAR DEFAULT '',
    payload JSON DEFAULT '{}',
    submitted_at TIMESTAMP WITH TIME ZONE,
    classification VARCHAR DEFAULT 'BILLING_SENSITIVE',
    training_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS billing_claim_events (
    id VARCHAR PRIMARY KEY,
    org_id VARCHAR NOT NULL,
    claim_id VARCHAR NOT NULL,
    event_type VARCHAR NOT NULL,
    from_status VARCHAR DEFAULT '',
    to_status VARCHAR NOT NULL,
    payload JSON DEFAULT '{}',
    classification VARCHAR DEFAULT 'BILLING_SENSITIVE',
    training_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS billing_payment_events (
    id VARCHAR PRIMARY KEY,
    org_id VARCHAR,
    payment_id VARCHAR,
    provider VARCHAR DEFAULT 'stripe',
    provider_event_id VARCHAR NOT NULL UNIQUE,
    event_type VARCHAR DEFAULT '',
    status VARCHAR DEFAULT 'received',
    payload JSON DEFAULT '{}',
    retry_count INTEGER DEFAULT 0,
    last_error VARCHAR DEFAULT '',
    classification VARCHAR DEFAULT 'BILLING_SENSITIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS billing_denials (
    id VARCHAR PRIMARY KEY,
    org_id VARCHAR NOT NULL,
    claim_id VARCHAR NOT NULL,
    reason VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'open',
    payload JSON DEFAULT '{}',
    classification VARCHAR DEFAULT 'BILLING_SENSITIVE',
    training_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS billing_appeals (
    id VARCHAR PRIMARY KEY,
    org_id VARCHAR NOT NULL,
    denial_id VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'draft',
    payload JSON DEFAULT '{}',
    classification VARCHAR DEFAULT 'BILLING_SENSITIVE',
    training_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS billing_facilities (
    id VARCHAR PRIMARY KEY,
    org_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    npi VARCHAR DEFAULT '',
    address VARCHAR DEFAULT '',
    status VARCHAR DEFAULT 'active',
    metadata JSON DEFAULT '{}',
    classification VARCHAR DEFAULT 'BILLING_SENSITIVE',
    training_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS billing_contacts (
    id VARCHAR PRIMARY KEY,
    org_id VARCHAR NOT NULL,
    facility_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    email VARCHAR DEFAULT '',
    phone VARCHAR DEFAULT '',
    role VARCHAR DEFAULT '',
    status VARCHAR DEFAULT 'active',
    metadata JSON DEFAULT '{}',
    classification VARCHAR DEFAULT 'BILLING_SENSITIVE',
    training_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS billing_contact_attempts (
    id VARCHAR PRIMARY KEY,
    org_id VARCHAR NOT NULL,
    contact_id VARCHAR NOT NULL,
    channel VARCHAR DEFAULT 'email',
    status VARCHAR DEFAULT 'queued',
    payload JSON DEFAULT '{}',
    attempted_at TIMESTAMP WITH TIME ZONE,
    classification VARCHAR DEFAULT 'BILLING_SENSITIVE',
    training_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS billing_patient_accounts (
    id VARCHAR PRIMARY KEY,
    org_id VARCHAR NOT NULL,
    patient_name VARCHAR NOT NULL,
    email VARCHAR DEFAULT '',
    phone VARCHAR DEFAULT '',
    status VARCHAR DEFAULT 'active',
    portal_token_hash VARCHAR DEFAULT '',
    portal_token_expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSON DEFAULT '{}',
    classification VARCHAR DEFAULT 'PHI',
    training_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS billing_documents (
    id VARCHAR PRIMARY KEY,
    org_id VARCHAR NOT NULL,
    invoice_id VARCHAR,
    payment_id VARCHAR,
    doc_type VARCHAR NOT NULL,
    storage_key VARCHAR NOT NULL,
    file_name VARCHAR DEFAULT '',
    content_type VARCHAR DEFAULT 'application/pdf',
    checksum VARCHAR DEFAULT '',
    metadata JSON DEFAULT '{}',
    classification VARCHAR DEFAULT 'BILLING_SENSITIVE',
    training_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS billing_portal_tokens (
    id VARCHAR PRIMARY KEY,
    org_id VARCHAR NOT NULL,
    patient_account_id VARCHAR NOT NULL,
    invoice_id VARCHAR NOT NULL,
    token_hash VARCHAR NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    classification VARCHAR DEFAULT 'PHI',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS comms_providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id VARCHAR NOT NULL,
    provider_type VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    config JSON DEFAULT '{}',
    status VARCHAR DEFAULT 'active',
    training_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS comms_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    channel VARCHAR DEFAULT 'email',
    subject VARCHAR DEFAULT '',
    body VARCHAR DEFAULT '',
    metadata JSON DEFAULT '{}',
    status VARCHAR DEFAULT 'active',
    training_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS comms_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id VARCHAR NOT NULL,
    message_id INTEGER,
    thread_id INTEGER,
    event_type VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'queued',
    payload JSON DEFAULT '{}',
    error VARCHAR DEFAULT '',
    training_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS comms_delivery_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id VARCHAR NOT NULL,
    event_id INTEGER NOT NULL,
    provider VARCHAR DEFAULT '',
    status VARCHAR DEFAULT 'pending',
    response_payload JSON DEFAULT '{}',
    error VARCHAR DEFAULT '',
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS carefusion_ledger_entries (
    id VARCHAR PRIMARY KEY,
    org_id INTEGER NOT NULL,
    entry_type VARCHAR DEFAULT 'debit',
    account VARCHAR DEFAULT 'telehealth_ar',
    amount INTEGER DEFAULT 0,
    currency VARCHAR DEFAULT 'usd',
    reference_type VARCHAR DEFAULT '',
    reference_id VARCHAR DEFAULT '',
    payload JSON DEFAULT '{}',
    classification VARCHAR DEFAULT 'BILLING_SENSITIVE',
    training_mode BOOLEAN DEFAULT FALSE,
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS carefusion_claims (
    id VARCHAR PRIMARY KEY,
    org_id INTEGER NOT NULL,
    encounter_id VARCHAR DEFAULT '',
    payer VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'draft',
    submission_reference VARCHAR DEFAULT '',
    payload JSON DEFAULT '{}',
    classification VARCHAR DEFAULT 'BILLING_SENSITIVE',
    training_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS carefusion_payer_routing (
    id VARCHAR PRIMARY KEY,
    org_id INTEGER NOT NULL,
    payer VARCHAR NOT NULL,
    route VARCHAR NOT NULL,
    rules JSON DEFAULT '{}',
    status VARCHAR DEFAULT 'active',
    classification VARCHAR DEFAULT 'BILLING_SENSITIVE',
    training_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS carefusion_audit_events (
    id VARCHAR PRIMARY KEY,
    org_id INTEGER NOT NULL,
    actor VARCHAR DEFAULT 'system',
    action VARCHAR NOT NULL,
    resource VARCHAR NOT NULL,
    before_state JSON DEFAULT '{}',
    after_state JSON DEFAULT '{}',
    classification VARCHAR DEFAULT 'BILLING_SENSITIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
