"""SaaS compliance refactor — rename tables, columns, add partner fields.

Revision ID: 003_saas_refactor
Revises: 002_add_paydunya_transactions
Create Date: 2026-02-10

This migration transitions the schema from insurance intermediary
to B2B SaaS platform model:
  - policies → coverage_subscriptions
  - premium_amount → partner_quoted_amount
  - coverage_type enum → partner_product_id string
  - escrow_segregated → routed_to_partner
  - Add partner_id and wali_role columns
  - Tax tracking: remove insurance metrics, add SaaS metrics
  - Add partner tables (partners, partner_invoices, platform_usage_logs, partner_api_configs)
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '003_saas_refactor'
down_revision: Union[str, Sequence[str], None] = '002_add_paydunya'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Rename: policies → coverage_subscriptions ─────────
    op.rename_table('policies', 'coverage_subscriptions')

    # Rename columns
    op.alter_column('coverage_subscriptions', 'premium_amount',
                    new_column_name='partner_quoted_amount')
    op.alter_column('coverage_subscriptions', 'policy_number',
                    new_column_name='subscription_number')

    # Drop old coverage_type enum column (was a PG enum), add string replacement
    op.drop_column('coverage_subscriptions', 'coverage_type')
    op.add_column('coverage_subscriptions',
                  sa.Column('partner_product_id', sa.String(100), nullable=True))
    op.add_column('coverage_subscriptions',
                  sa.Column('partner_id', sa.String(50), nullable=True))

    # Drop check constraint on premium_amount (now partner_quoted_amount)
    op.drop_constraint('positive_premium', 'coverage_subscriptions', type_='check')
    op.create_check_constraint(
        'positive_quoted_amount', 'coverage_subscriptions',
        'partner_quoted_amount > 0'
    )

    # ── 2. Financial events: add partner fields, rename columns ────
    op.alter_column('financial_events', 'escrow_segregated',
                    new_column_name='routed_to_partner')
    op.alter_column('financial_events', 'policy_id',
                    new_column_name='subscription_id')
    op.add_column('financial_events',
                  sa.Column('partner_id', sa.String(50), nullable=True))
    op.add_column('financial_events',
                  sa.Column('wali_role', sa.String(50),
                            server_default='technology_provider', nullable=True))

    # ── 3. Tax exemption tracking: remove insurance, add SaaS ────
    op.drop_column('tax_exemption_tracking', 'total_premiums_collected')
    op.drop_column('tax_exemption_tracking', 'total_claims_paid')
    op.drop_column('tax_exemption_tracking', 'loss_ratio')
    op.drop_column('tax_exemption_tracking', 'cosumaf_report_status')

    op.add_column('tax_exemption_tracking',
                  sa.Column('saas_subscription_revenue', sa.Integer(), server_default='0'))
    op.add_column('tax_exemption_tracking',
                  sa.Column('platform_service_revenue', sa.Integer(), server_default='0'))
    op.add_column('tax_exemption_tracking',
                  sa.Column('total_payments_routed', sa.Integer(), server_default='0'))
    op.add_column('tax_exemption_tracking',
                  sa.Column('total_incidents_forwarded', sa.Integer(), server_default='0'))

    # ── 4. Create partner tables ─────────────────────────────
    op.create_table('partners',
        sa.Column('id', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('partner_type', sa.String(50), server_default='insurer'),
        sa.Column('api_endpoint', sa.String(500), nullable=True),
        sa.Column('api_key_encrypted', sa.Text(), nullable=True),
        sa.Column('payment_account', sa.String(200), nullable=True),
        sa.Column('monthly_license_fee', sa.Integer(), server_default='0'),
        sa.Column('contract_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('contract_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('partner_invoices',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('partner_id', sa.String(50), nullable=False),
        sa.Column('invoice_number', sa.String(100), nullable=False),
        sa.Column('billing_period_start', sa.Date(), nullable=False),
        sa.Column('billing_period_end', sa.Date(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(3), server_default='XOF'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invoice_number'),
    )

    op.create_table('platform_usage_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('partner_id', sa.String(50), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('api_calls', sa.Integer(), server_default='0'),
        sa.Column('active_artisans', sa.Integer(), server_default='0'),
        sa.Column('enrollments_created', sa.Integer(), server_default='0'),
        sa.Column('incidents_reported', sa.Integer(), server_default='0'),
        sa.Column('payments_routed', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── 5. Update FK references ──────────────────────────────
    # claims table refs policies — update to coverage_subscriptions
    # Note: if FK constraint exists, it will auto-follow table rename in PG
    # But the column name still says policy_id — that's fine for backward compat


def downgrade() -> None:
    # ── Reverse partner tables ───────────────────────────────
    op.drop_table('platform_usage_logs')
    op.drop_table('partner_invoices')
    op.drop_table('partners')

    # ── Reverse tax tracking ─────────────────────────────────
    op.drop_column('tax_exemption_tracking', 'total_incidents_forwarded')
    op.drop_column('tax_exemption_tracking', 'total_payments_routed')
    op.drop_column('tax_exemption_tracking', 'platform_service_revenue')
    op.drop_column('tax_exemption_tracking', 'saas_subscription_revenue')

    op.add_column('tax_exemption_tracking',
                  sa.Column('cosumaf_report_status', sa.String(20)))
    op.add_column('tax_exemption_tracking',
                  sa.Column('loss_ratio', sa.Numeric(5, 2)))
    op.add_column('tax_exemption_tracking',
                  sa.Column('total_claims_paid', sa.Integer(), server_default='0'))
    op.add_column('tax_exemption_tracking',
                  sa.Column('total_premiums_collected', sa.Integer(), server_default='0'))

    # ── Reverse financial events ─────────────────────────────
    op.drop_column('financial_events', 'wali_role')
    op.drop_column('financial_events', 'partner_id')
    op.alter_column('financial_events', 'subscription_id',
                    new_column_name='policy_id')
    op.alter_column('financial_events', 'routed_to_partner',
                    new_column_name='escrow_segregated')

    # ── Reverse coverage_subscriptions → policies ────────────
    op.drop_column('coverage_subscriptions', 'partner_id')
    op.drop_column('coverage_subscriptions', 'partner_product_id')
    op.add_column('coverage_subscriptions',
                  sa.Column('coverage_type',
                            sa.Enum('HEALTH', 'EQUIPMENT', 'THEFT', 'BUNDLE', name='coveragetype'),
                            nullable=True))

    op.drop_constraint('positive_quoted_amount', 'coverage_subscriptions', type_='check')
    op.create_check_constraint(
        'positive_premium', 'coverage_subscriptions',
        'premium_amount > 0'
    )

    op.alter_column('coverage_subscriptions', 'subscription_number',
                    new_column_name='policy_number')
    op.alter_column('coverage_subscriptions', 'partner_quoted_amount',
                    new_column_name='premium_amount')

    op.rename_table('coverage_subscriptions', 'policies')
