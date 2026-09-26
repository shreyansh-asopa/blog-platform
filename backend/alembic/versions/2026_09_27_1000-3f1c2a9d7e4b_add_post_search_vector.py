"""add post search vector

Revision ID: 3f1c2a9d7e4b
Revises: 57d92805f126
Create Date: 2026-09-27 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "3f1c2a9d7e4b"
down_revision: str | Sequence[str] | None = "57d92805f126"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # A generated column: Postgres fills it in for existing rows now, and recomputes it
    # on every insert or update, so the app never has to remember to
    op.add_column(
        "posts",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "setweight(to_tsvector('english', title), 'A') || "
                "setweight(to_tsvector('english', content), 'B')",
                persisted=True,
            ),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_posts_search_vector",
        "posts",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_posts_search_vector", table_name="posts", postgresql_using="gin")
    op.drop_column("posts", "search_vector")
