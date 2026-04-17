"""add created_at and updated_at to chat_sessions

Revision ID: 30dbfa1a671f
Revises: 0ddd0844b936
Create Date: 2026-04-17 13:16:36.110853

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '30dbfa1a671f'
down_revision = '0ddd0844b936'
branch_labels = None
depends_on = None


from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        "chat_sessions",
        sa.Column("created_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "chat_sessions",
        sa.Column("updated_at", sa.DateTime(), nullable=True)
    )

    op.execute("""
        UPDATE chat_sessions
        SET created_at = started_at
        WHERE created_at IS NULL
    """)

    op.execute("""
        UPDATE chat_sessions
        SET updated_at = started_at
        WHERE updated_at IS NULL
    """)

    op.alter_column("chat_sessions", "created_at", nullable=False)
    op.alter_column("chat_sessions", "updated_at", nullable=False)


def downgrade():
    op.drop_column("chat_sessions", "updated_at")
    op.drop_column("chat_sessions", "created_at")