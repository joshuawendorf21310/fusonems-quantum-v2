"""
Alembic migration for TransportDocumentSnapshot table
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from typing import Union, Sequence

revision: str = "20260125_transport"
down_revision: Union[str, Sequence[str], None] = "bd39170c3e32"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'transport_document_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('org_id', sa.Integer(), nullable=False, index=True),
        sa.Column('trip_id', sa.Integer(), nullable=False, index=True),
        sa.Column('doc_type', sa.String(), nullable=False, index=True),
        sa.Column('file_id', sa.String(), nullable=True),
        sa.Column('extracted_json', sa.JSON(), nullable=False),
        sa.Column('confidence_json', sa.JSON(), nullable=False),
        sa.Column('evidence_json', sa.JSON(), nullable=False),
        sa.Column('warnings_json', sa.JSON(), nullable=True),
        sa.Column('provider', sa.String(), nullable=False, server_default='deterministic'),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, index=True),
    )
    op.create_index('ix_transport_document_snapshots_org_id', 'transport_document_snapshots', ['org_id'])
    op.create_index('ix_transport_document_snapshots_trip_id', 'transport_document_snapshots', ['trip_id'])
    op.create_index('ix_transport_document_snapshots_doc_type', 'transport_document_snapshots', ['doc_type'])
    op.create_index('ix_transport_document_snapshots_created_at', 'transport_document_snapshots', ['created_at'])

def downgrade():
    op.drop_table('transport_document_snapshots')
