"""add post content format

Revision ID: cb7e639c9357
Revises: b7d2e4f19a60
Create Date: 2026-09-28 01:55:30.577308

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cb7e639c9357"
down_revision: str | Sequence[str] | None = "b7d2e4f19a60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

content_format = sa.Enum("markdown", "html", name="content_format")


def upgrade() -> None:
    # Every existing post was written in Markdown, so that is the default
    content_format.create(op.get_bind())
    op.add_column(
        "posts",
        sa.Column("content_format", content_format, server_default="markdown", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("posts", "content_format")
    content_format.drop(op.get_bind())
