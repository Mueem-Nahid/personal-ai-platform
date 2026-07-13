"""create initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-13

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS \"uuid-ossp\"")
    op.execute("DROP EXTENSION IF EXISTS vector")
