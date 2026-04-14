"""Add review_cycles, performance_goals tables and extend performance_reviews

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-13 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    # --- review_cycles table ---
    op.create_table(
        'review_cycles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('self_assessment_deadline', sa.Date(), nullable=True),
        sa.Column('manager_review_deadline', sa.Date(), nullable=True),
        sa.Column('status', sa.String(20), server_default='draft'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Extend performance_reviews with cycle-based columns ---
    op.add_column('performance_reviews', sa.Column('cycle_id', sa.Integer(), sa.ForeignKey('review_cycles.id', ondelete='SET NULL'), nullable=True))
    op.add_column('performance_reviews', sa.Column('self_assessment', JSONB(), nullable=True))
    op.add_column('performance_reviews', sa.Column('manager_assessment', JSONB(), nullable=True))
    op.add_column('performance_reviews', sa.Column('composite_score', sa.Numeric(5, 2), nullable=True))
    op.add_column('performance_reviews', sa.Column('final_comments', sa.Text(), nullable=True))

    op.create_index('ix_perf_review_cycle', 'performance_reviews', ['cycle_id'])

    # --- performance_goals table ---
    op.create_table(
        'performance_goals',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('review_id', sa.Integer(), sa.ForeignKey('performance_reviews.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('weight', sa.Numeric(5, 2), nullable=False),
        sa.Column('target', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_perf_goal_review', 'performance_goals', ['review_id'])


def downgrade():
    op.drop_index('ix_perf_goal_review', table_name='performance_goals')
    op.drop_table('performance_goals')
    op.drop_index('ix_perf_review_cycle', table_name='performance_reviews')
    op.drop_column('performance_reviews', 'final_comments')
    op.drop_column('performance_reviews', 'composite_score')
    op.drop_column('performance_reviews', 'manager_assessment')
    op.drop_column('performance_reviews', 'self_assessment')
    op.drop_column('performance_reviews', 'cycle_id')
    op.drop_table('review_cycles')
