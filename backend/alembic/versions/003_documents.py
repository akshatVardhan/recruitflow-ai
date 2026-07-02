"""create documents table

Revision ID: 003
Revises: 002
Create Date: 2026-07-02

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE document_type AS ENUM ("
        "'resume', 'job_description', 'offer_letter', 'sop', "
        "'performance_report', 'policy', 'contract', 'other')"
    )

    op.create_table(
        "documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("doc_type", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("file_size_kb", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("auto_tags", postgresql.JSONB(), nullable=True),
        sa.Column("manual_tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_documents_client_id", "documents", ["client_id"])
    op.create_index("idx_documents_user_id", "documents", ["user_id"])
    op.create_index("idx_documents_doc_type", "documents", ["doc_type"])
    op.create_index(
        "idx_documents_created_at", "documents", [sa.text("created_at DESC")]
    )
    op.execute(
        "CREATE INDEX idx_documents_fts ON documents "
        "USING gin(to_tsvector('english', title || ' ' || coalesce(extracted_text, '')))"
    )


def downgrade() -> None:
    op.drop_index(
        "idx_documents_fts", table_name="documents", postgresql_concurrently=False
    )
    op.drop_index("idx_documents_created_at", table_name="documents")
    op.drop_index("idx_documents_doc_type", table_name="documents")
    op.drop_index("idx_documents_user_id", table_name="documents")
    op.drop_index("idx_documents_client_id", table_name="documents")
    op.drop_table("documents")
    op.execute("DROP TYPE IF EXISTS document_type")
