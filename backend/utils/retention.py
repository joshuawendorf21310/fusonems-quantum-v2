from models.quantum_documents import RetentionPolicy


DEFAULT_RETENTION_POLICIES = [
    {
        "name": "Clinical Records",
        "applies_to": "clinical",
        "retention_days": 365 * 7,
        "delete_behavior": "soft_delete",
        "legal_hold_behavior": "always_freeze",
    },
    {
        "name": "Billing Records",
        "applies_to": "billing",
        "retention_days": 365 * 7,
        "delete_behavior": "soft_delete",
        "legal_hold_behavior": "always_freeze",
    },
    {
        "name": "Legal Records",
        "applies_to": "legal",
        "retention_days": 365 * 10,
        "delete_behavior": "soft_delete",
        "legal_hold_behavior": "always_freeze",
    },
    {
        "name": "Operations Records",
        "applies_to": "ops",
        "retention_days": 365 * 2,
        "delete_behavior": "soft_delete",
        "legal_hold_behavior": "always_freeze",
    },
    {
        "name": "Training & QA",
        "applies_to": "training_qa",
        "retention_days": 365 * 5,
        "delete_behavior": "soft_delete",
        "legal_hold_behavior": "always_freeze",
    },
    {
        "name": "Comms Billing Calls",
        "applies_to": "comms_billing",
        "retention_days": 365 * 7,
        "delete_behavior": "soft_delete",
        "legal_hold_behavior": "always_freeze",
    },
    {
        "name": "Comms Ops Calls",
        "applies_to": "comms_ops",
        "retention_days": 365 * 2,
        "delete_behavior": "soft_delete",
        "legal_hold_behavior": "always_freeze",
    },
    {
        "name": "Email Ops",
        "applies_to": "email_ops",
        "retention_days": 365 * 2,
        "delete_behavior": "soft_delete",
        "legal_hold_behavior": "always_freeze",
    },
    {
        "name": "Email Billing",
        "applies_to": "email_billing",
        "retention_days": 365 * 7,
        "delete_behavior": "soft_delete",
        "legal_hold_behavior": "always_freeze",
    },
    {
        "name": "Email Legal",
        "applies_to": "email_legal",
        "retention_days": 365 * 10,
        "delete_behavior": "soft_delete",
        "legal_hold_behavior": "always_freeze",
    },
]


def seed_retention_policies(db, org_id: int) -> None:
    existing = db.query(RetentionPolicy).filter(RetentionPolicy.org_id == org_id).first()
    if existing:
        return
    for policy in DEFAULT_RETENTION_POLICIES:
        db.add(RetentionPolicy(org_id=org_id, **policy))
    db.commit()
