"""add_resource_allocations_table

Revision ID: l7m8n9o0p1q2
Revises: k6l7m8n9o0p1
Create Date: 2026-04-13

"""
from alembic import op
import sqlalchemy as sa

revision = 'l7m8n9o0p1q2'
down_revision = 'k6l7m8n9o0p1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'resource_allocations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('employee_id', sa.Integer(), sa.ForeignKey('employees.id'), nullable=False),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('allocation_percent', sa.Numeric(5, 2), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('company_users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint('allocation_percent > 0 AND allocation_percent <= 100',
                           name='ck_resource_alloc_percent_range'),
        sa.CheckConstraint('start_date <= end_date', name='ck_resource_alloc_dates'),
    )
    op.create_index('ix_resource_allocations_employee', 'resource_allocations', ['employee_id'])
    op.create_index('ix_resource_allocations_project', 'resource_allocations', ['project_id'])
    op.create_index('ix_resource_allocations_dates', 'resource_allocations', ['start_date', 'end_date'])


def downgrade():
    op.drop_index('ix_resource_allocations_dates', table_name='resource_allocations')
    op.drop_index('ix_resource_allocations_project', table_name='resource_allocations')
    op.drop_index('ix_resource_allocations_employee', table_name='resource_allocations')
    op.drop_table('resource_allocations')
