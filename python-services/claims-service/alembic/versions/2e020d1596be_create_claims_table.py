"""create claims table

Revision ID: 2e020d1596be
Revises: 
Create Date: 2026-02-02 12:27:15.407625

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = '2e020d1596be'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    # Create transactions if not exists (Skipped to avoid conflicts)
    # if 'transactions' not in tables:
    #     op.create_table('transactions',
    #         sa.Column('id', sa.UUID(), nullable=False),
    #         sa.PrimaryKeyConstraint('id')
    #     )

    # Drop claims if exists to avoid conflicts
    if 'claims' in tables:
        op.drop_table('claims')
        
    # Drop types if they exist (to avoid DuplicateObject error)
    op.execute("DROP TYPE IF EXISTS claimstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS coveragetype CASCADE")

    # Recreate claims table from scratch
    op.create_table('claims',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('user_id', sa.String(128), nullable=False),
        sa.Column('policy_id', sa.UUID(), nullable=False),
        sa.Column('claim_number', sa.String(length=50), nullable=False, unique=True),
        sa.Column('claim_type', sa.Enum('HEALTH', 'EQUIPMENT', 'THEFT', 'BUNDLE', name='coveragetype'), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('claimed_amount', sa.Integer(), nullable=False),
        sa.Column('approved_amount', sa.Integer(), nullable=True),
        sa.Column('image_urls', sa.ARRAY(sa.Text()), nullable=True),
        sa.Column('image_hashes', sa.ARRAY(sa.Text()), nullable=True),
        sa.Column('exif_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.Enum('SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'PAID', name='claimstatus'), default='SUBMITTED'),
        sa.Column('reviewer_id', sa.String(128), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('fraud_score', sa.Integer(), default=0),
        sa.Column('fraud_flags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('payout_transaction_id', sa.UUID(), nullable=True),
        sa.Column('payout_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        
        # Foreign Keys
        # sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        # sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        # sa.ForeignKeyConstraint(['reviewer_id'], ['users.id']),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('claims')
