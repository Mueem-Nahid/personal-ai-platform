"""create job_posts table

Revision ID: 7f2678117e74
Revises: c4ae2e1e9056
Create Date: 2026-07-19 01:22:11.195304

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '7f2678117e74'
down_revision: Union[str, None] = 'c4ae2e1e9056'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('job_posts',
    sa.Column('url', sa.String(length=1000), nullable=True),
    sa.Column('title', sa.String(length=500), nullable=True),
    sa.Column('company', sa.String(length=500), nullable=True),
    sa.Column('location', sa.String(length=500), nullable=True),
    sa.Column('source', sa.String(length=20), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('raw_text', sa.Text(), nullable=True),
    sa.Column('parsed_fields', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_job_posts_url', 'job_posts', ['url'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_job_posts_url', table_name='job_posts')
    op.drop_table('job_posts')
