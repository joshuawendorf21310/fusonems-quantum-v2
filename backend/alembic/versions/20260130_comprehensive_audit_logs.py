"""Add comprehensive audit logs table for FedRAMP compliance

Revision ID: 20260130_comprehensive_audit
Revises: 20260130_cascade_indexes
Create Date: 2026-01-30

This migration creates the comprehensive_audit_logs table for FedRAMP AU-2, AU-3, AU-9 compliance.
The table is designed for:
- Immutable, write-only audit logging
- 7-year retention per FedRAMP requirements
- High-performance querying with appropriate indexes
- Partitioning support (can be added later for very large deployments)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260130_comprehensive_audit"
down_revision: Union[str, Sequence[str], None] = "20260130_cascade_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create comprehensive_audit_logs table with all required indexes"""
    
    # Create the comprehensive_audit_logs table
    op.create_table(
        "comprehensive_audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("user_email", sa.String(length=255), nullable=True),
        sa.Column("user_role", sa.String(length=100), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("outcome", sa.String(length=50), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("request_method", sa.String(length=10), nullable=True),
        sa.Column("request_path", sa.String(length=1000), nullable=True),
        sa.Column("request_query", sa.String(length=2000), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("device_id", sa.String(length=255), nullable=True),
        sa.Column("device_fingerprint", sa.String(length=255), nullable=True),
        sa.Column("classification", sa.String(length=50), nullable=True),
        sa.Column("training_mode", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("before_state", postgresql.JSON(), nullable=True),
        sa.Column("after_state", postgresql.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
        sa.Column("reason_code", sa.String(length=100), nullable=True),
        sa.Column("decision_id", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    
    # Create indexes for performance
    op.create_index("idx_audit_timestamp", "comprehensive_audit_logs", ["timestamp"])
    op.create_index("idx_audit_user_org", "comprehensive_audit_logs", ["user_id", "org_id"])
    op.create_index("idx_audit_event_type", "comprehensive_audit_logs", ["event_type"])
    op.create_index("idx_audit_outcome", "comprehensive_audit_logs", ["outcome"])
    op.create_index("idx_audit_resource", "comprehensive_audit_logs", ["resource_type", "resource_id"])
    op.create_index("idx_audit_ip", "comprehensive_audit_logs", ["ip_address"])
    op.create_index("idx_audit_date_user", "comprehensive_audit_logs", ["timestamp", "user_id"])
    op.create_index("idx_audit_date_org", "comprehensive_audit_logs", ["timestamp", "org_id"])
    op.create_index("idx_audit_compliance", "comprehensive_audit_logs", ["org_id", "event_type", "outcome", "timestamp"])
    op.create_index("ix_comprehensive_audit_logs_org_id", "comprehensive_audit_logs", ["org_id"])
    op.create_index("ix_comprehensive_audit_logs_user_id", "comprehensive_audit_logs", ["user_id"])
    op.create_index("ix_comprehensive_audit_logs_user_email", "comprehensive_audit_logs", ["user_email"])
    op.create_index("ix_comprehensive_audit_logs_event_type", "comprehensive_audit_logs", ["event_type"])
    op.create_index("ix_comprehensive_audit_logs_action", "comprehensive_audit_logs", ["action"])
    op.create_index("ix_comprehensive_audit_logs_resource_type", "comprehensive_audit_logs", ["resource_type"])
    op.create_index("ix_comprehensive_audit_logs_resource_id", "comprehensive_audit_logs", ["resource_id"])
    op.create_index("ix_comprehensive_audit_logs_outcome", "comprehensive_audit_logs", ["outcome"])
    op.create_index("ix_comprehensive_audit_logs_ip_address", "comprehensive_audit_logs", ["ip_address"])
    op.create_index("ix_comprehensive_audit_logs_request_path", "comprehensive_audit_logs", ["request_path"])
    op.create_index("ix_comprehensive_audit_logs_session_id", "comprehensive_audit_logs", ["session_id"])
    op.create_index("ix_comprehensive_audit_logs_device_id", "comprehensive_audit_logs", ["device_id"])
    op.create_index("ix_comprehensive_audit_logs_timestamp", "comprehensive_audit_logs", ["timestamp"])
    
    # Create a function to prevent UPDATE/DELETE operations (immutability enforcement)
    # Note: This is a best-effort enforcement. Database-level triggers should also be
    # configured in production for stronger enforcement.
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_log_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Audit logs are immutable and cannot be modified or deleted';
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger to prevent UPDATE operations
    op.execute("""
        CREATE TRIGGER prevent_audit_log_update
        BEFORE UPDATE ON comprehensive_audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_log_modification();
    """)
    
    # Create trigger to prevent DELETE operations
    op.execute("""
        CREATE TRIGGER prevent_audit_log_delete
        BEFORE DELETE ON comprehensive_audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_log_modification();
    """)


def downgrade() -> None:
    """Drop comprehensive_audit_logs table and related objects"""
    
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS prevent_audit_log_delete ON comprehensive_audit_logs;")
    op.execute("DROP TRIGGER IF EXISTS prevent_audit_log_update ON comprehensive_audit_logs;")
    
    # Drop function
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_log_modification();")
    
    # Drop indexes
    op.drop_index("ix_comprehensive_audit_logs_timestamp", table_name="comprehensive_audit_logs")
    op.drop_index("ix_comprehensive_audit_logs_device_id", table_name="comprehensive_audit_logs")
    op.drop_index("ix_comprehensive_audit_logs_session_id", table_name="comprehensive_audit_logs")
    op.drop_index("ix_comprehensive_audit_logs_request_path", table_name="comprehensive_audit_logs")
    op.drop_index("ix_comprehensive_audit_logs_ip_address", table_name="comprehensive_audit_logs")
    op.drop_index("ix_comprehensive_audit_logs_outcome", table_name="comprehensive_audit_logs")
    op.drop_index("ix_comprehensive_audit_logs_resource_id", table_name="comprehensive_audit_logs")
    op.drop_index("ix_comprehensive_audit_logs_resource_type", table_name="comprehensive_audit_logs")
    op.drop_index("ix_comprehensive_audit_logs_action", table_name="comprehensive_audit_logs")
    op.drop_index("ix_comprehensive_audit_logs_event_type", table_name="comprehensive_audit_logs")
    op.drop_index("ix_comprehensive_audit_logs_user_email", table_name="comprehensive_audit_logs")
    op.drop_index("ix_comprehensive_audit_logs_user_id", table_name="comprehensive_audit_logs")
    op.drop_index("ix_comprehensive_audit_logs_org_id", table_name="comprehensive_audit_logs")
    op.drop_index("idx_audit_compliance", table_name="comprehensive_audit_logs")
    op.drop_index("idx_audit_date_org", table_name="comprehensive_audit_logs")
    op.drop_index("idx_audit_date_user", table_name="comprehensive_audit_logs")
    op.drop_index("idx_audit_ip", table_name="comprehensive_audit_logs")
    op.drop_index("idx_audit_resource", table_name="comprehensive_audit_logs")
    op.drop_index("idx_audit_outcome", table_name="comprehensive_audit_logs")
    op.drop_index("idx_audit_event_type", table_name="comprehensive_audit_logs")
    op.drop_index("idx_audit_user_org", table_name="comprehensive_audit_logs")
    op.drop_index("idx_audit_timestamp", table_name="comprehensive_audit_logs")
    
    # Drop table
    op.drop_table("comprehensive_audit_logs")
