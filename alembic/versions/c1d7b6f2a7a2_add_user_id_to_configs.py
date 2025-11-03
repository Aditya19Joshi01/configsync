"""Add user_id columns to service_configs and config_versions

Revision ID: c1d7b6f2a7a2
Revises: ca2c96fc9683
Create Date: 2025-11-03 15:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import Integer

# revision identifiers, used by Alembic.
revision = 'c1d7b6f2a7a2'
down_revision = 'ca2c96fc9683'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Add nullable user_id columns to both tables
    op.add_column('service_configs', sa.Column('user_id', sa.Integer(), nullable=True))
    op.add_column('config_versions', sa.Column('user_id', sa.Integer(), nullable=True))

    # 2) If there are existing users, choose a default owner; otherwise leave NULL.
    #    We avoid forcing NOT NULL until we can backfill in a safe manner.

    # 3) Create an index on (name, user_id) and (service_name, user_id)
    op.create_index(op.f('ix_service_configs_name_user_id'), 'service_configs', ['name', 'user_id'], unique=False)
    op.create_index(op.f('ix_config_versions_service_user'), 'config_versions', ['service_name', 'user_id'], unique=False)

    # 4) Create a foreign key constraint if users table exists.
    try:
        op.create_foreign_key('fk_service_configs_user_id_users', 'service_configs', 'users', ['user_id'], ['id'])
        op.create_foreign_key('fk_config_versions_user_id_users', 'config_versions', 'users', ['user_id'], ['id'])
    except Exception:
        # If the users table does not exist or DB restricts FK creation at this point,
        # we continue; user should ensure DB is in correct state and run a second migration
        pass


def downgrade() -> None:
    # Drop the foreign keys and indexes then the columns
    try:
        op.drop_constraint('fk_service_configs_user_id_users', 'service_configs', type_='foreignkey')
    except Exception:
        pass
    try:
        op.drop_constraint('fk_config_versions_user_id_users', 'config_versions', type_='foreignkey')
    except Exception:
        pass
    op.drop_index(op.f('ix_service_configs_name_user_id'), table_name='service_configs')
    op.drop_index(op.f('ix_config_versions_service_user'), table_name='config_versions')
    op.drop_column('service_configs', 'user_id')
    op.drop_column('config_versions', 'user_id')

