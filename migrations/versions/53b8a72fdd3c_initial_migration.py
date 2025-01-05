"""Initial migration

Revision ID: 53b8a72fdd3c
Revises: 
Create Date: 2025-01-02 20:03:00.097032

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '53b8a72fdd3c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nickname', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False, unique=True),
        sa.Column('password', sa.String(length=200), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_title', sa.String(length=255), nullable=False),
        sa.Column('company', sa.String(length=255), nullable=False),
        sa.Column('job_post_link', sa.Text(), nullable=True),
        sa.Column('salary', sa.Numeric(10, 2), nullable=True),
        sa.Column('location_type', sa.String(length=50), nullable=True),
        sa.Column('job_type', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('date_created', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('job_description', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), sa.ForeignKey('jobs.id'), nullable=False),
        sa.Column('stage', sa.String(length=50), nullable=False),
        sa.Column('note_text', sa.Text(), nullable=False),
        sa.Column('date_created', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), sa.ForeignKey('jobs.id'), nullable=False),
        sa.Column('stage', sa.String(length=50), nullable=False),
        sa.Column('document_name', sa.String(length=255), nullable=False),
        sa.Column('document_url', sa.String(length=255), nullable=False),
        sa.Column('date_uploaded', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('documents')
    op.drop_table('notes')
    op.drop_table('jobs')
    op.drop_table('users')

