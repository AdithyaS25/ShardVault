"""create_vault_entries_table

Revision ID: 0002_vault_entries
Revises: 0001_add_encryption_salt
Create Date: 2026-03-12

Per §2.1 database schema — vault_entries table.
Stores metadata only. Encrypted payload lives on share nodes.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0002_vault_entries'
down_revision = '4e33ce0f0e04'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'vault_entries',
        sa.Column('id',         postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id',    postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('site_name',  sa.String(),  nullable=False),
        sa.Column('username',   sa.String(),  nullable=False),
        sa.Column('label',      sa.String(),  nullable=True),
        sa.Column('encrypted_payload_length', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    op.create_index('ix_vault_entries_user_id', 'vault_entries', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_vault_entries_user_id', table_name='vault_entries')
    op.drop_table('vault_entries')
