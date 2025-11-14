"""Initial schema for AI Training Service

Revision ID: 001
Revises:
Create Date: 2025-01-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create session_status enum
    session_status_enum = postgresql.ENUM('active', 'completed', 'abandoned', name='sessionstatus', create_type=True)
    session_status_enum.create(op.get_bind(), checkfirst=True)

    # Create message_role enum
    message_role_enum = postgresql.ENUM('system', 'user', 'assistant', name='messagerole', create_type=True)
    message_role_enum.create(op.get_bind(), checkfirst=True)

    # Create chat_sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('status', session_status_enum, nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_sessions_id'), 'chat_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_chat_sessions_user_id'), 'chat_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_chat_sessions_topic_id'), 'chat_sessions', ['topic_id'], unique=False)
    op.create_index(op.f('ix_chat_sessions_course_id'), 'chat_sessions', ['course_id'], unique=False)

    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('role', message_role_enum, nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_messages_id'), 'chat_messages', ['id'], unique=False)
    op.create_index(op.f('ix_chat_messages_session_id'), 'chat_messages', ['session_id'], unique=False)

    # Create session_contexts table
    op.create_table(
        'session_contexts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('user_level', sa.String(length=50), nullable=True),
        sa.Column('completed_topics_json', sa.Text(), nullable=True),
        sa.Column('struggles_json', sa.Text(), nullable=True),
        sa.Column('course_title', sa.String(length=255), nullable=True),
        sa.Column('topic_title', sa.String(length=255), nullable=True),
        sa.Column('learning_objectives', sa.Text(), nullable=True),
        sa.Column('prompt_template', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    op.create_index(op.f('ix_session_contexts_id'), 'session_contexts', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_index(op.f('ix_session_contexts_id'), table_name='session_contexts')
    op.drop_table('session_contexts')

    op.drop_index(op.f('ix_chat_messages_session_id'), table_name='chat_messages')
    op.drop_index(op.f('ix_chat_messages_id'), table_name='chat_messages')
    op.drop_table('chat_messages')

    op.drop_index(op.f('ix_chat_sessions_course_id'), table_name='chat_sessions')
    op.drop_index(op.f('ix_chat_sessions_topic_id'), table_name='chat_sessions')
    op.drop_index(op.f('ix_chat_sessions_user_id'), table_name='chat_sessions')
    op.drop_index(op.f('ix_chat_sessions_id'), table_name='chat_sessions')
    op.drop_table('chat_sessions')

    # Drop enums
    sa.Enum(name='messagerole').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='sessionstatus').drop(op.get_bind(), checkfirst=True)
