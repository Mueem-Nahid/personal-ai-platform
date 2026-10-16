"""create master_resumes and resume_versions tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-07

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = '0006'
down_revision: str | None = '0005'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'master_resumes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('profile_id', UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(20), server_default=sa.text("'active'"), nullable=False),
        sa.Column('is_default', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('profile_id', 'document_id', name='uq_master_resumes_profile_doc'),
    )
    op.create_index('ix_master_resumes_profile_id', 'master_resumes', ['profile_id'])

    op.create_table(
        'resume_versions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('profile_id', UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', UUID(as_uuid=True), sa.ForeignKey('job_posts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('master_resume_id', UUID(as_uuid=True), sa.ForeignKey('master_resumes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_no', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), server_default=sa.text("'building'"), nullable=False),
        sa.Column('content_json', JSONB(), nullable=True),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('prompt_text', sa.Text(), nullable=True),
        sa.Column('evidence_text', sa.Text(), nullable=True),
        sa.Column('raw_response', sa.Text(), nullable=True),
        sa.Column('top_k_chunk_ids', JSONB(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('provider', sa.String(20), nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('prompt_version', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('profile_id', 'job_id', 'version_no', name='uq_resume_versions_profile_job_version'),
    )
    op.create_index('ix_resume_versions_profile_id', 'resume_versions', ['profile_id'])
    op.create_index('ix_resume_versions_job_id', 'resume_versions', ['job_id'])
    op.create_index('ix_resume_versions_status', 'resume_versions', ['status'])


def downgrade() -> None:
    op.drop_index('ix_resume_versions_status', table_name='resume_versions')
    op.drop_index('ix_resume_versions_job_id', table_name='resume_versions')
    op.drop_index('ix_resume_versions_profile_id', table_name='resume_versions')
    op.drop_table('resume_versions')
    op.drop_index('ix_master_resumes_profile_id', table_name='master_resumes')
    op.drop_table('master_resumes')
