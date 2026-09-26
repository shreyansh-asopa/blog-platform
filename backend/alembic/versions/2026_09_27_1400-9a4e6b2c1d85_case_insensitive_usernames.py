"""case-insensitive usernames

Revision ID: 9a4e6b2c1d85
Revises: 3f1c2a9d7e4b
Create Date: 2026-09-27 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9a4e6b2c1d85"
down_revision: str | Sequence[str] | None = "3f1c2a9d7e4b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # The new index would fail on names that differ only in case, with a vaguer error.
    # Stop with a clear one instead, so someone decides which account gets renamed.
    clashes = (
        op.get_bind()
        .scalars(sa.text("SELECT lower(username) FROM users GROUP BY 1 HAVING count(*) > 1"))
        .all()
    )
    if clashes:
        raise RuntimeError(f"Usernames differ only in case, rename them first: {clashes}")

    # Replaces the exact-match constraint: lower(username) is also what lookups search on
    op.drop_constraint(op.f("uq_users_username"), "users", type_="unique")
    op.create_index(
        "uq_users_username_lower", "users", [sa.literal_column("lower(username)")], unique=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_users_username_lower", table_name="users")
    op.create_unique_constraint(op.f("uq_users_username"), "users", ["username"])
