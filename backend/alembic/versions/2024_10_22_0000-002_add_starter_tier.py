"""Add starter tier to plan_tier enum

Revision ID: 002
Revises: 001
Create Date: 2024-10-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 'starter' value to plan_tier enum
    # Note: This operation is not reversible in a transaction
    op.execute("ALTER TYPE plan_tier ADD VALUE IF NOT EXISTS 'starter'")


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values easily
    # In production, you'd need to:
    # 1. Create new enum without 'starter'
    # 2. Alter column to use new enum
    # 3. Drop old enum
    # For now, we'll just pass (this is acceptable for MVP)
    pass
