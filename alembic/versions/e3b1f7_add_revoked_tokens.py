"""Add revoked_tokens table

Revision ID: e3b1f7_add_revoked_tokens
Revises: d2e8c9b4f1
Create Date: 2025-11-03 15:50:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e3b1f7_add_revoked_tokens'
down_revision = 'd2e8c9b4f1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'revoked_tokens',
        sa.Column('jti', sa.String(), primary_key=True, nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
    )
    op.create_index(op.f('ix_revoked_tokens_jti'), 'revoked_tokens', ['jti'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_revoked_tokens_jti'), table_name='revoked_tokens')
    op.drop_table('revoked_tokens')

