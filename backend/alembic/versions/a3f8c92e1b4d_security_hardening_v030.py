"""security_hardening_v030

Add token_blocklist table for JWT revocation and
must_change_password column to users table.

Revision ID: a3f8c92e1b4d
Revises: fab2bc20d58c
Create Date: 2026-09-23 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3f8c92e1b4d'
down_revision: Union[str, None] = 'fab2bc20d58c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Create token_blocklist table ---
    op.create_table(
        'token_blocklist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('jti', sa.String(length=64), nullable=False),
        sa.Column('user_email', sa.String(length=255), nullable=False),
        sa.Column('blocked_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reason', sa.String(length=128), nullable=False, server_default='logout'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('jti'),
    )
    op.create_index(op.f('ix_token_blocklist_id'), 'token_blocklist', ['id'], unique=False)
    op.create_index(op.f('ix_token_blocklist_jti'), 'token_blocklist', ['jti'], unique=True)
    op.create_index(op.f('ix_token_blocklist_user_email'), 'token_blocklist', ['user_email'], unique=False)

    # --- Add must_change_password column to users ---
    op.add_column('users', sa.Column(
        'must_change_password',
        sa.Boolean(),
        nullable=False,
        server_default=sa.text('0'),
    ))


def downgrade() -> None:
    # --- Remove must_change_password column ---
    op.drop_column('users', 'must_change_password')

    # --- Drop token_blocklist table ---
    op.drop_index(op.f('ix_token_blocklist_user_email'), table_name='token_blocklist')
    op.drop_index(op.f('ix_token_blocklist_jti'), table_name='token_blocklist')
    op.drop_index(op.f('ix_token_blocklist_id'), table_name='token_blocklist')
    op.drop_table('token_blocklist')
