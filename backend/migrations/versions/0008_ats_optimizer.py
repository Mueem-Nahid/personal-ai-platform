"""Store ATS evaluations and versioned refinement snapshots.

Revision ID: 0008
Revises: 0007
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resume_versions", sa.Column("ats_report", JSONB(), nullable=True))
    op.add_column("resume_versions", sa.Column("optimization_context", JSONB(), nullable=True))
    op.add_column("resume_versions", sa.Column("ats_baseline_score", sa.Integer(), nullable=True))
    op.add_column(
        "resume_versions", sa.Column("parent_version_id", UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        "fk_resume_versions_parent",
        "resume_versions",
        "resume_versions",
        ["parent_version_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_resume_versions_parent", "resume_versions", type_="foreignkey")
    for column in ("parent_version_id", "ats_baseline_score", "optimization_context", "ats_report"):
        op.drop_column("resume_versions", column)
