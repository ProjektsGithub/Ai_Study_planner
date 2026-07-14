"""merge_heads

Revision ID: 56f1edb77a05
Revises: 6c4ec519a8aa, e8a9c7f3d512, f2a3b8c9d401
Create Date: 2026-07-14 22:51:40.212082

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '56f1edb77a05'
down_revision: Union[str, Sequence[str], None] = ('6c4ec519a8aa', 'e8a9c7f3d512', 'f2a3b8c9d401')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
