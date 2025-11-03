"""Add role column to users

Revision ID: d2e8c9b4f1
Revises: c1d7b6f2a7a2
Create Date: 2025-11-03 15:20:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd2e8c9b4f1'
down_revision = 'c1d7b6f2a7a2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # add role column with default 'user'
    op.add_column('users', sa.Column('role', sa.String(), nullable=False, server_default='user'))
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_role'), table_name='users')
    op.drop_column('users', 'role')

