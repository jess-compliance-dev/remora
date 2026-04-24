"""add topic_summary and facts_count to chat_analysis

Revision ID: 2bc8284fe344
Revises: 7984b1114b5d
Create Date: 2026-04-23 15:34:11.966787

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2bc8284fe344'
down_revision = '7984b1114b5d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("chat_analysis", schema=None) as batch_op:
        batch_op.add_column(sa.Column("topic_summary", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("facts_count", sa.Integer(), nullable=False, server_default="0"))

    op.execute("UPDATE chat_analysis SET facts_count = 0 WHERE facts_count IS NULL")

    with op.batch_alter_table("chat_analysis", schema=None) as batch_op:
        batch_op.alter_column("facts_count", server_default=None)


def downgrade():
    with op.batch_alter_table("chat_analysis", schema=None) as batch_op:
        batch_op.drop_column("facts_count")
        batch_op.drop_column("topic_summary")