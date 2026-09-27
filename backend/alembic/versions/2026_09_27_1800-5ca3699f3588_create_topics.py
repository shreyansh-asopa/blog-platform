"""create topics

Revision ID: 5ca3699f3588
Revises: 9a4e6b2c1d85
Create Date: 2026-09-27 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5ca3699f3588"
down_revision: str | Sequence[str] | None = "9a4e6b2c1d85"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The curated list. Part of the schema, so every database (not just seeded ones) has it
TOPICS = [
    ("ai", "AI", "Models, agents and the ideas behind artificial intelligence."),
    ("genai", "Generative AI", "LLMs, prompting, RAG and building products on generative models."),
    ("machine-learning", "Machine Learning", "Training, evaluating and shipping models."),
    ("data-engineering", "Data Engineering", "Pipelines, warehouses, streaming and data quality."),
    ("software-engineering", "Software Engineering", "Design, testing and code that lasts."),
    ("cloud-devops", "Cloud & DevOps", "Infrastructure, CI/CD, containers and production."),
    ("web-development", "Web Development", "Frontend, backend and everything a browser loads."),
    ("security", "Security", "Keeping systems, data and people safe."),
]


def upgrade() -> None:
    """Upgrade schema."""
    topics = op.create_table(
        "topics",
        sa.Column("slug", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint("slug", name=op.f("pk_topics")),
    )
    op.create_table(
        "post_topics",
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column("topic_slug", sa.String(length=40), nullable=False),
        sa.ForeignKeyConstraint(
            ["post_id"],
            ["posts.id"],
            name=op.f("fk_post_topics_post_id_posts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["topic_slug"],
            ["topics.slug"],
            name=op.f("fk_post_topics_topic_slug_topics"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("post_id", "topic_slug", name=op.f("pk_post_topics")),
    )
    op.create_index(op.f("ix_post_topics_topic_slug"), "post_topics", ["topic_slug"], unique=False)
    op.bulk_insert(
        topics,
        [
            {"slug": slug, "name": name, "description": description, "position": position}
            for position, (slug, name, description) in enumerate(TOPICS, start=1)
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_post_topics_topic_slug"), table_name="post_topics")
    op.drop_table("post_topics")
    op.drop_table("topics")
