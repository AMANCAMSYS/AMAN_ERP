"""add_timesheet_entries_table

Revision ID: k6l7m8n9o0p1
Revises: j5k6l7m8n9o0
Create Date: 2026-04-13

"""
from alembic import op
import sqlalchemy as sa

revision = 'k6l7m8n9o0p1'
down_revision = 'j5k6l7m8n9o0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'timesheet_entries',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('employee_id', sa.Integer(), sa.ForeignKey('employees.id'), nullable=False),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('project_tasks.id'), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('hours', sa.Numeric(5, 2), nullable=False),
        sa.Column('is_billable', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('billing_rate', sa.Numeric(18, 4), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('approved_by', sa.Integer(), sa.ForeignKey('employees.id'), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('company_users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint('hours > 0 AND hours <= 24', name='ck_timesheet_hours_range'),
        sa.CheckConstraint("status IN ('draft', 'submitted', 'approved', 'rejected')", name='ck_timesheet_status'),
    )
    op.create_index('ix_timesheet_entries_employee_date', 'timesheet_entries', ['employee_id', 'date'])
    op.create_index('ix_timesheet_entries_project', 'timesheet_entries', ['project_id'])
    op.create_index('ix_timesheet_entries_status', 'timesheet_entries', ['status'])


def downgrade():
    op.drop_index('ix_timesheet_entries_status', table_name='timesheet_entries')
    op.drop_index('ix_timesheet_entries_project', table_name='timesheet_entries')
    op.drop_index('ix_timesheet_entries_employee_date', table_name='timesheet_entries')
    op.drop_table('timesheet_entries')
