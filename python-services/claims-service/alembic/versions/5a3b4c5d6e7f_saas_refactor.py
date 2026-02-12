"""SaaS compliance refactor — rename claims table to incident_reports.

Revision ID: 5a3b4c5d6e7f
Revises: 4a2b3c4d5e6f
Create Date: 2026-02-10

Renames claims → incident_reports and updates columns to reflect
that Wali forwards incident data to partner insurers, not processes claims.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '5a3b4c5d6e7f_saas_refactor'
down_revision: Union[str, Sequence[str], None] = '4a2b3c4d5e6f_create_financial_events'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Rename: claims → incident_reports ─────────────────────
    op.rename_table('claims', 'incident_reports')

    # Rename columns
    op.alter_column('incident_reports', 'claim_type',
                    new_column_name='incident_type')
    op.alter_column('incident_reports', 'claim_number',
                    new_column_name='incident_number')
    op.alter_column('incident_reports', 'claimed_amount',
                    new_column_name='reported_amount')
    op.alter_column('incident_reports', 'approved_amount',
                    new_column_name='partner_approved_amount')
    op.alter_column('incident_reports', 'policy_id',
                    new_column_name='subscription_id')

    # Add partner columns
    op.add_column('incident_reports',
                  sa.Column('partner_id', sa.String(50), nullable=True))
    op.add_column('incident_reports',
                  sa.Column('partner_reference', sa.String(200), nullable=True))
    op.add_column('incident_reports',
                  sa.Column('forwarded_to_partner_at', sa.DateTime(timezone=True), nullable=True))

    # Update status enum values (claim-specific → incident-specific)
    # In PG, we need to update the enum type or use string column
    # Since the model already uses strings, we just need to update existing rows
    op.execute("""
        UPDATE incident_reports SET status = 'partner_paid' WHERE status = 'paid';
    """)


def downgrade() -> None:
    # Reverse status update
    op.execute("""
        UPDATE incident_reports SET status = 'paid' WHERE status = 'partner_paid';
    """)

    # Drop partner columns
    op.drop_column('incident_reports', 'forwarded_to_partner_at')
    op.drop_column('incident_reports', 'partner_reference')
    op.drop_column('incident_reports', 'partner_id')

    # Rename columns back
    op.alter_column('incident_reports', 'subscription_id',
                    new_column_name='policy_id')
    op.alter_column('incident_reports', 'partner_approved_amount',
                    new_column_name='approved_amount')
    op.alter_column('incident_reports', 'reported_amount',
                    new_column_name='claimed_amount')
    op.alter_column('incident_reports', 'incident_number',
                    new_column_name='claim_number')
    op.alter_column('incident_reports', 'incident_type',
                    new_column_name='claim_type')

    # Rename table back
    op.rename_table('incident_reports', 'claims')
