"""Add paydunya_transactions table

Revision ID: 002_add_paydunya
Revises: b33c8b45afbc
Create Date: 2026-02-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = "002_add_paydunya"
down_revision = "b33c8b45afbc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "paydunya_transactions",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("internal_ref", sa.String(100), nullable=False),
        sa.Column("paydunya_token", sa.String(255), nullable=True),
        sa.Column("paydunya_invoice_url", sa.String(500), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("amount_customer_paid", sa.Integer(), nullable=True),
        sa.Column("paydunya_fees", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("provider_used", sa.String(50), nullable=True),
        sa.Column("policy_id", UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", sa.String(128), nullable=True),
        sa.Column("customer_phone", sa.String(20), nullable=True),
        sa.Column("customer_name", sa.String(100), nullable=True),
        sa.Column("raw_webhook_data", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("internal_ref"),
        sa.UniqueConstraint("paydunya_token"),
        sa.ForeignKeyConstraint(["policy_id"], ["policies.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    # Performance indexes
    op.create_index("idx_paydunya_status", "paydunya_transactions", ["status"])
    op.create_index("idx_paydunya_policy", "paydunya_transactions", ["policy_id"])
    op.create_index("idx_paydunya_user", "paydunya_transactions", ["user_id"])
    op.create_index("idx_paydunya_ref", "paydunya_transactions", ["internal_ref"])


def downgrade() -> None:
    op.drop_index("idx_paydunya_ref", table_name="paydunya_transactions")
    op.drop_index("idx_paydunya_user", table_name="paydunya_transactions")
    op.drop_index("idx_paydunya_policy", table_name="paydunya_transactions")
    op.drop_index("idx_paydunya_status", table_name="paydunya_transactions")
    op.drop_table("paydunya_transactions")
