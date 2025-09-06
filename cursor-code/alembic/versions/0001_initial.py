"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2025-09-03

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.create_table(
		'users',
		sa.Column('id', sa.Integer(), primary_key=True),
		sa.Column('email', sa.String(length=255), nullable=False, unique=True, index=True),
		sa.Column('coins', sa.Integer(), nullable=False, server_default='200'),
		sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
	)

	op.create_table(
		'sharks',
		sa.Column('id', sa.Integer(), primary_key=True),
		sa.Column('name', sa.String(length=100), nullable=False),
		sa.Column('price_coins', sa.Integer(), nullable=False),
		sa.Column('personality', sa.String(length=255), nullable=False),
		sa.Column('expertise', sa.String(length=255), nullable=False),
		sa.Column('image_url', sa.String(length=255), nullable=False),
		sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
	)

	op.create_table(
		'chat_sessions',
		sa.Column('id', sa.Integer(), primary_key=True),
		sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
		sa.Column('shark_id', sa.Integer(), sa.ForeignKey('sharks.id'), nullable=False),
		sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
		sa.Column('report', sa.Text(), nullable=True),
		sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
		sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
	)

	op.create_table(
		'messages',
		sa.Column('id', sa.Integer(), primary_key=True),
		sa.Column('session_id', sa.Integer(), sa.ForeignKey('chat_sessions.id'), nullable=False, index=True),
		sa.Column('sender', sa.String(length=20), nullable=False),
		sa.Column('content', sa.Text(), nullable=False),
		sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
	)

	op.create_table(
		'purchases',
		sa.Column('id', sa.Integer(), primary_key=True),
		sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
		sa.Column('coins', sa.Integer(), nullable=False),
		sa.Column('usd_amount', sa.Integer(), nullable=False),
		sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
	)


def downgrade() -> None:
	op.drop_table('purchases')
	op.drop_table('messages')
	op.drop_table('chat_sessions')
	op.drop_table('sharks')
	op.drop_table('users')
