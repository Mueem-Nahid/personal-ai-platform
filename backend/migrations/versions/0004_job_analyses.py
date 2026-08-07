"""create job_analyses table

Revision ID: 0004
Revises: 7f2678117e74
Create Date: 2026-07-26

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = '0004'
down_revision: str | None = '7f2678117e74'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'job_analyses',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('job_id', UUID(as_uuid=True), sa.ForeignKey('job_posts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('profile_id', UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(20), server_default=sa.text("'analyzing'"), nullable=False),
        sa.Column('report', JSONB(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('provider', sa.String(20), nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('prompt_version', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('job_id', 'profile_id', name='uq_job_analyses_job_profile'),
    )
    op.create_index('ix_job_analyses_job_id', 'job_analyses', ['job_id'])
    op.create_index('ix_job_analyses_profile_id', 'job_analyses', ['profile_id'])
    op.create_index('ix_job_analyses_status', 'job_analyses', ['status'])


def downgrade() -> None:
    op.drop_index('ix_job_analyses_status', table_name='job_analyses')
    op.drop_index('ix_job_analyses_profile_id', table_name='job_analyses')
    op.drop_index('ix_job_analyses_job_id', table_name='job_analyses')
    op.drop_table('job_analyses')
