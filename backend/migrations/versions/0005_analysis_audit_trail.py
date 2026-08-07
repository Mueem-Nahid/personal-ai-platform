"""add audit trail columns to job_analyses

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-26

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0005'
down_revision: str | None = '0004'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('job_analyses', sa.Column('prompt_text', sa.Text(), nullable=True))
    op.add_column('job_analyses', sa.Column('evidence_text', sa.Text(), nullable=True))
    op.add_column('job_analyses', sa.Column('raw_response', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('job_analyses', 'raw_response')
    op.drop_column('job_analyses', 'evidence_text')
    op.drop_column('job_analyses', 'prompt_text')
