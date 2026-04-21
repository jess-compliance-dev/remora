"""remove chatbot prompt dependency

Revision ID: 20dfd980a148
Revises: 29efc0546883
Create Date: 2026-04-21 13:43:49.576918
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '20dfd980a148'
down_revision = '29efc0546883'
branch_labels = None
depends_on = None


def upgrade():
    # 1. FIRST: remove FK + column from chat_messages
    with op.batch_alter_table('chat_messages', schema=None) as batch_op:
        batch_op.drop_constraint(
            'chat_messages_related_prompt_id_fkey',
            type_='foreignkey'
        )
        batch_op.drop_column('related_prompt_id')

    # 2. THEN: drop table
    op.drop_table('chatbot_prompts')

    # 3. Optional: keep your schema improvements (safe to keep)
    with op.batch_alter_table('chat_messages', schema=None) as batch_op:
        batch_op.alter_column(
            'role',
            existing_type=sa.VARCHAR(length=50),
            type_=sa.String(length=20),
            existing_nullable=False
        )
        batch_op.alter_column(
            'message_text',
            existing_type=sa.TEXT(),
            nullable=False
        )
        batch_op.alter_column(
            'audio_url',
            existing_type=sa.TEXT(),
            type_=sa.String(length=500),
            existing_nullable=True
        )
        batch_op.alter_column(
            'message_order',
            existing_type=sa.INTEGER(),
            nullable=False
        )
        batch_op.alter_column(
            'created_at',
            existing_type=postgresql.TIMESTAMP(),
            nullable=True
        )


def downgrade():
    # 1. recreate chatbot_prompts
    op.create_table(
        'chatbot_prompts',
        sa.Column('prompt_id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('category', sa.VARCHAR(length=100), nullable=True),
        sa.Column('question_text', sa.TEXT(), nullable=False),
        sa.Column('life_period', sa.VARCHAR(length=100), nullable=True),
        sa.Column('is_active', sa.BOOLEAN(), nullable=False),
        sa.Column('sort_order', sa.INTEGER(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(), nullable=False),
        sa.PrimaryKeyConstraint('prompt_id', name=op.f('chatbot_prompts_pkey'))
    )

    # 2. restore column + FK
    with op.batch_alter_table('chat_messages', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('related_prompt_id', sa.INTEGER(), nullable=True)
        )
        batch_op.create_foreign_key(
            'chat_messages_related_prompt_id_fkey',
            'chatbot_prompts',
            ['related_prompt_id'],
            ['prompt_id'],
            ondelete='SET NULL'
        )

        # rollback schema changes
        batch_op.alter_column(
            'created_at',
            existing_type=postgresql.TIMESTAMP(),
            nullable=False
        )
        batch_op.alter_column(
            'message_order',
            existing_type=sa.INTEGER(),
            nullable=True
        )
        batch_op.alter_column(
            'audio_url',
            existing_type=sa.String(length=500),
            type_=sa.TEXT(),
            existing_nullable=True
        )
        batch_op.alter_column(
            'message_text',
            existing_type=sa.TEXT(),
            nullable=True
        )
        batch_op.alter_column(
            'role',
            existing_type=sa.String(length=20),
            type_=sa.VARCHAR(length=50),
            existing_nullable=False
        )
