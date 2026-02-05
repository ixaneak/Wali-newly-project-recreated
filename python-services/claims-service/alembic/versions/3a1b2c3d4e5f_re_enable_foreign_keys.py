"""re-enable foreign keys

Revision ID: 3a1b2c3d4e5f
Revises: 2e020d1596be
Create Date: 2026-02-03 02:38:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3a1b2c3d4e5f'
down_revision: Union[str, Sequence[str], None] = '2e020d1596be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Re-enable foreign key constraints on claims table."""
    # First, clean up orphaned data (claims without valid users)
    op.execute("""
        DELETE FROM claims 
        WHERE user_id NOT IN (SELECT id FROM users)
    """)
    
    # Clean up claims without valid policies
    op.execute("""
        DELETE FROM claims 
        WHERE policy_id NOT IN (SELECT id FROM policies)
    """)
    
    # Re-create the foreign key for user_id
    op.create_foreign_key(
        'fk_claims_user_id',
        'claims', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Re-create the foreign key for policy_id
    op.create_foreign_key(
        'fk_claims_policy_id',
        'claims', 'policies',
        ['policy_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Re-create the foreign key for reviewer_id (nullable)
    op.create_foreign_key(
        'fk_claims_reviewer_id',
        'claims', 'users',
        ['reviewer_id'], ['id']
    )


def downgrade() -> None:
    """Remove foreign key constraints."""
    op.drop_constraint('fk_claims_user_id', 'claims', type_='foreignkey')
    op.drop_constraint('fk_claims_policy_id', 'claims', type_='foreignkey')
    op.drop_constraint('fk_claims_reviewer_id', 'claims', type_='foreignkey')
