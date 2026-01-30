"""add_metriport_tables

Revision ID: 20260127_metriport_integration
Revises: 20260126_023717_add_storage_tables
Create Date: 2026-01-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260127_metriport_integration'
down_revision = '20260126_023717'
branch_labels = None
depends_on = None


def upgrade():
    # Create patient_insurance table
    op.create_table(
        'patient_insurance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('master_patient_id', sa.Integer(), nullable=True),
        sa.Column('epcr_patient_id', sa.Integer(), nullable=True),
        sa.Column('coverage_type', sa.Enum('PRIMARY', 'SECONDARY', 'TERTIARY', name='insurancecoveragetype'), nullable=True),
        sa.Column('payer_name', sa.String(), nullable=False),
        sa.Column('payer_id', sa.String(), nullable=True),
        sa.Column('member_id', sa.String(), nullable=False),
        sa.Column('group_number', sa.String(), nullable=True),
        sa.Column('plan_name', sa.String(), nullable=True),
        sa.Column('verification_status', sa.Enum('PENDING', 'VERIFIED', 'FAILED', 'MANUAL_REVIEW', 'EXPIRED', name='insuranceverificationstatus'), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_source', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('coverage_start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('coverage_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('copay_amount', sa.String(), nullable=True),
        sa.Column('deductible_amount', sa.String(), nullable=True),
        sa.Column('deductible_met', sa.String(), nullable=True),
        sa.Column('out_of_pocket_max', sa.String(), nullable=True),
        sa.Column('out_of_pocket_met', sa.String(), nullable=True),
        sa.Column('policy_holder_name', sa.String(), nullable=True),
        sa.Column('policy_holder_dob', sa.String(), nullable=True),
        sa.Column('relationship_to_patient', sa.String(), nullable=True),
        sa.Column('raw_eligibility_response', sa.JSON(), nullable=False),
        sa.Column('classification', sa.String(), nullable=True),
        sa.Column('training_mode', sa.Boolean(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('last_verification_attempt', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['epcr_patient_id'], ['epcr_patients.id'], ),
        sa.ForeignKeyConstraint(['master_patient_id'], ['master_patients.id'], ),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patient_insurance_coverage_type'), 'patient_insurance', ['coverage_type'], unique=False)
    op.create_index(op.f('ix_patient_insurance_epcr_patient_id'), 'patient_insurance', ['epcr_patient_id'], unique=False)
    op.create_index(op.f('ix_patient_insurance_master_patient_id'), 'patient_insurance', ['master_patient_id'], unique=False)
    op.create_index(op.f('ix_patient_insurance_member_id'), 'patient_insurance', ['member_id'], unique=False)
    op.create_index(op.f('ix_patient_insurance_org_id'), 'patient_insurance', ['org_id'], unique=False)
    op.create_index(op.f('ix_patient_insurance_verification_status'), 'patient_insurance', ['verification_status'], unique=False)

    # Create metriport_patient_mapping table
    op.create_table(
        'metriport_patient_mapping',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('master_patient_id', sa.Integer(), nullable=True),
        sa.Column('epcr_patient_id', sa.Integer(), nullable=True),
        sa.Column('metriport_patient_id', sa.String(), nullable=False),
        sa.Column('metriport_facility_id', sa.String(), nullable=True),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('date_of_birth', sa.String(), nullable=False),
        sa.Column('gender', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('address', sa.JSON(), nullable=False),
        sa.Column('mapping_confidence', sa.Integer(), nullable=True),
        sa.Column('mapping_source', sa.String(), nullable=True),
        sa.Column('mapping_verified', sa.Boolean(), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sync_status', sa.Enum('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', name='metriportsyncstatus'), nullable=True),
        sa.Column('classification', sa.String(), nullable=True),
        sa.Column('training_mode', sa.Boolean(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['epcr_patient_id'], ['epcr_patients.id'], ),
        sa.ForeignKeyConstraint(['master_patient_id'], ['master_patients.id'], ),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_metriport_patient_mapping_epcr_patient_id'), 'metriport_patient_mapping', ['epcr_patient_id'], unique=False)
    op.create_index(op.f('ix_metriport_patient_mapping_master_patient_id'), 'metriport_patient_mapping', ['master_patient_id'], unique=False)
    op.create_index(op.f('ix_metriport_patient_mapping_metriport_patient_id'), 'metriport_patient_mapping', ['metriport_patient_id'], unique=True)
    op.create_index(op.f('ix_metriport_patient_mapping_org_id'), 'metriport_patient_mapping', ['org_id'], unique=False)
    op.create_index(op.f('ix_metriport_patient_mapping_sync_status'), 'metriport_patient_mapping', ['sync_status'], unique=False)

    # Create metriport_webhook_events table
    op.create_table(
        'metriport_webhook_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('webhook_id', sa.String(), nullable=True),
        sa.Column('metriport_patient_id', sa.String(), nullable=True),
        sa.Column('raw_payload', sa.JSON(), nullable=False),
        sa.Column('processed', sa.Boolean(), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_metriport_webhook_events_event_type'), 'metriport_webhook_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_metriport_webhook_events_metriport_patient_id'), 'metriport_webhook_events', ['metriport_patient_id'], unique=False)
    op.create_index(op.f('ix_metriport_webhook_events_org_id'), 'metriport_webhook_events', ['org_id'], unique=False)
    op.create_index(op.f('ix_metriport_webhook_events_processed'), 'metriport_webhook_events', ['processed'], unique=False)
    op.create_index(op.f('ix_metriport_webhook_events_received_at'), 'metriport_webhook_events', ['received_at'], unique=False)

    # Create metriport_document_sync table
    op.create_table(
        'metriport_document_sync',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('metriport_patient_id', sa.String(), nullable=False),
        sa.Column('master_patient_id', sa.Integer(), nullable=True),
        sa.Column('document_id', sa.String(), nullable=False),
        sa.Column('document_type', sa.Enum('C_CDA', 'CONSOLIDATED_CDA', 'DIAGNOSTIC_REPORT', 'DOCUMENT_REFERENCE', name='fhirdocumenttype'), nullable=True),
        sa.Column('document_title', sa.String(), nullable=True),
        sa.Column('document_description', sa.Text(), nullable=True),
        sa.Column('document_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('facility_name', sa.String(), nullable=True),
        sa.Column('facility_npi', sa.String(), nullable=True),
        sa.Column('file_url', sa.String(), nullable=True),
        sa.Column('local_storage_path', sa.String(), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('file_hash', sa.String(), nullable=True),
        sa.Column('fhir_bundle', sa.JSON(), nullable=False),
        sa.Column('parsed_data', sa.JSON(), nullable=False),
        sa.Column('sync_status', sa.Enum('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', name='metriportsyncstatus'), nullable=True),
        sa.Column('downloaded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('parsed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('classification', sa.String(), nullable=True),
        sa.Column('training_mode', sa.Boolean(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['master_patient_id'], ['master_patients.id'], ),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_metriport_document_sync_document_id'), 'metriport_document_sync', ['document_id'], unique=True)
    op.create_index(op.f('ix_metriport_document_sync_master_patient_id'), 'metriport_document_sync', ['master_patient_id'], unique=False)
    op.create_index(op.f('ix_metriport_document_sync_metriport_patient_id'), 'metriport_document_sync', ['metriport_patient_id'], unique=False)
    op.create_index(op.f('ix_metriport_document_sync_org_id'), 'metriport_document_sync', ['org_id'], unique=False)
    op.create_index(op.f('ix_metriport_document_sync_sync_status'), 'metriport_document_sync', ['sync_status'], unique=False)

    # Create insurance_verification_log table
    op.create_table(
        'insurance_verification_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('patient_insurance_id', sa.Integer(), nullable=True),
        sa.Column('master_patient_id', sa.Integer(), nullable=True),
        sa.Column('verification_type', sa.String(), nullable=True),
        sa.Column('verification_status', sa.Enum('PENDING', 'VERIFIED', 'FAILED', 'MANUAL_REVIEW', 'EXPIRED', name='insuranceverificationstatus'), nullable=True),
        sa.Column('request_payload', sa.JSON(), nullable=False),
        sa.Column('response_payload', sa.JSON(), nullable=False),
        sa.Column('is_eligible', sa.Boolean(), nullable=True),
        sa.Column('eligibility_message', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('initiated_by', sa.Integer(), nullable=True),
        sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['initiated_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['master_patient_id'], ['master_patients.id'], ),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['patient_insurance_id'], ['patient_insurance.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_insurance_verification_log_master_patient_id'), 'insurance_verification_log', ['master_patient_id'], unique=False)
    op.create_index(op.f('ix_insurance_verification_log_org_id'), 'insurance_verification_log', ['org_id'], unique=False)
    op.create_index(op.f('ix_insurance_verification_log_patient_insurance_id'), 'insurance_verification_log', ['patient_insurance_id'], unique=False)
    op.create_index(op.f('ix_insurance_verification_log_requested_at'), 'insurance_verification_log', ['requested_at'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_insurance_verification_log_requested_at'), table_name='insurance_verification_log')
    op.drop_index(op.f('ix_insurance_verification_log_patient_insurance_id'), table_name='insurance_verification_log')
    op.drop_index(op.f('ix_insurance_verification_log_org_id'), table_name='insurance_verification_log')
    op.drop_index(op.f('ix_insurance_verification_log_master_patient_id'), table_name='insurance_verification_log')
    op.drop_table('insurance_verification_log')
    
    op.drop_index(op.f('ix_metriport_document_sync_sync_status'), table_name='metriport_document_sync')
    op.drop_index(op.f('ix_metriport_document_sync_org_id'), table_name='metriport_document_sync')
    op.drop_index(op.f('ix_metriport_document_sync_metriport_patient_id'), table_name='metriport_document_sync')
    op.drop_index(op.f('ix_metriport_document_sync_master_patient_id'), table_name='metriport_document_sync')
    op.drop_index(op.f('ix_metriport_document_sync_document_id'), table_name='metriport_document_sync')
    op.drop_table('metriport_document_sync')
    
    op.drop_index(op.f('ix_metriport_webhook_events_received_at'), table_name='metriport_webhook_events')
    op.drop_index(op.f('ix_metriport_webhook_events_processed'), table_name='metriport_webhook_events')
    op.drop_index(op.f('ix_metriport_webhook_events_org_id'), table_name='metriport_webhook_events')
    op.drop_index(op.f('ix_metriport_webhook_events_metriport_patient_id'), table_name='metriport_webhook_events')
    op.drop_index(op.f('ix_metriport_webhook_events_event_type'), table_name='metriport_webhook_events')
    op.drop_table('metriport_webhook_events')
    
    op.drop_index(op.f('ix_metriport_patient_mapping_sync_status'), table_name='metriport_patient_mapping')
    op.drop_index(op.f('ix_metriport_patient_mapping_org_id'), table_name='metriport_patient_mapping')
    op.drop_index(op.f('ix_metriport_patient_mapping_metriport_patient_id'), table_name='metriport_patient_mapping')
    op.drop_index(op.f('ix_metriport_patient_mapping_master_patient_id'), table_name='metriport_patient_mapping')
    op.drop_index(op.f('ix_metriport_patient_mapping_epcr_patient_id'), table_name='metriport_patient_mapping')
    op.drop_table('metriport_patient_mapping')
    
    op.drop_index(op.f('ix_patient_insurance_verification_status'), table_name='patient_insurance')
    op.drop_index(op.f('ix_patient_insurance_org_id'), table_name='patient_insurance')
    op.drop_index(op.f('ix_patient_insurance_member_id'), table_name='patient_insurance')
    op.drop_index(op.f('ix_patient_insurance_master_patient_id'), table_name='patient_insurance')
    op.drop_index(op.f('ix_patient_insurance_epcr_patient_id'), table_name='patient_insurance')
    op.drop_index(op.f('ix_patient_insurance_coverage_type'), table_name='patient_insurance')
    op.drop_table('patient_insurance')
    
    # Drop enums
    sa.Enum(name='insuranceverificationstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='insurancecoveragetype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='metriportsyncstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='fhirdocumenttype').drop(op.get_bind(), checkfirst=True)
