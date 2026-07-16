"""
add_password_reset_fields

Revision ID: a1b2c3d4e5f6
Revises: 56f1edb77a05
Create Date: 2026-07-16

Ajout des colonnes reset_password_token et reset_password_token_expires
sur la table users pour le flux de réinitialisation du mot de passe.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'a1b2c3d4e5f6'
down_revision = '56f1edb77a05'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('reset_password_token', sa.String(255), nullable=True),
    )
    op.add_column(
        'users',
        sa.Column('reset_password_token_expires', sa.DateTime(), nullable=True),
    )
    op.create_index(
        'ix_users_reset_password_token',
        'users',
        ['reset_password_token'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_users_reset_password_token', table_name='users')
    op.drop_column('users', 'reset_password_token_expires')
    op.drop_column('users', 'reset_password_token')
