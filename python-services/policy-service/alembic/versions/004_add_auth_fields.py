"""Add auth fields to User

Revision ID: 004_add_auth_fields
Revises: 003_saas_refactor
Create Date: 2026-02-18

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_add_auth_fields'
down_revision: Union[str, Sequence[str], None] = '003_saas_refactor'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('email', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=True))
    op.create_unique_constraint(None, 'users', ['email'])


def downgrade() -> None:
    op.drop_constraint(None, 'users', type_='unique')
    op.drop_column('users', 'password_hash')
    op.drop_column('users', 'email')
