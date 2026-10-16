"""create resume_templates and render_jobs tables

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-18

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = '0007'
down_revision: str | None = '0006'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'resume_templates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('profile_id', UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=True),
        sa.Column('builtin_key', sa.String(100), nullable=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('format', sa.String(10), nullable=False),
        sa.Column('source_text', sa.Text(), nullable=True),
        sa.Column('styles_text', sa.Text(), nullable=True),
        sa.Column('asset_key', sa.String(500), nullable=True),
        sa.Column('is_default', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('status', sa.String(20), server_default=sa.text("'active'"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_resume_templates_profile_id', 'resume_templates', ['profile_id'])
    op.create_index('ux_resume_templates_builtin_key', 'resume_templates', ['builtin_key'], unique=True)

    op.create_table(
        'render_jobs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('profile_id', UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('template_id', UUID(as_uuid=True), sa.ForeignKey('resume_templates.id', ondelete='SET NULL'), nullable=True),
        sa.Column('resume_version_id', UUID(as_uuid=True), sa.ForeignKey('resume_versions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('content_json', JSONB(), nullable=True),
        sa.Column('output_format', sa.String(10), nullable=False),
        sa.Column('engine', sa.String(40), nullable=True),
        sa.Column('status', sa.String(20), server_default=sa.text("'queued'"), nullable=False),
        sa.Column('minio_object_key', sa.String(500), nullable=True),
        sa.Column('filename', sa.String(255), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_render_jobs_profile_id', 'render_jobs', ['profile_id'])
    op.create_index('ix_render_jobs_resume_version_id', 'render_jobs', ['resume_version_id'])
    op.create_index('ix_render_jobs_status', 'render_jobs', ['status'])


def downgrade() -> None:
    op.drop_index('ix_render_jobs_status', table_name='render_jobs')
    op.drop_index('ix_render_jobs_resume_version_id', table_name='render_jobs')
    op.drop_index('ix_render_jobs_profile_id', table_name='render_jobs')
    op.drop_table('render_jobs')
    op.drop_index('ux_resume_templates_builtin_key', table_name='resume_templates')
    op.drop_index('ix_resume_templates_profile_id', table_name='resume_templates')
    op.drop_table('resume_templates')
