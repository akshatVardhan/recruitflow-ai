"""add status column to documents

Revision ID: 006
Revises: 005
Create Date: 2026-07-11

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("status", sa.String(), nullable=False, server_default="uploaded"),
    )
    op.create_index("idx_documents_status", "documents", ["status"])


def downgrade() -> None:
    op.drop_index("idx_documents_status", table_name="documents")
    op.drop_column("documents", "status")
