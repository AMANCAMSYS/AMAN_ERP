"""add cashflow forecast tables

Revision ID: a7b8c9d0e1f2
Revises: f1a2b3c4d5e6
Create Date: 2026-04-03
"""
from alembic import op
import sqlalchemy as sa

revision = 'a7b8c9d0e1f2'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'cashflow_forecasts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('forecast_date', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=False),
        sa.Column('horizon_days', sa.Integer(), server_default='90', nullable=False),
        sa.Column('mode', sa.String(20), server_default="'contractual'", nullable=False),
        sa.Column('generated_by', sa.Integer(),
                  sa.ForeignKey('company_users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        'cashflow_forecast_lines',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('forecast_id', sa.Integer(),
                  sa.ForeignKey('cashflow_forecasts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('bank_account_id', sa.Integer(),
                  sa.ForeignKey('treasury_accounts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_type', sa.String(20), nullable=False),
        sa.Column('source_document_id', sa.Integer(), nullable=True),
        sa.Column('projected_inflow', sa.Numeric(18, 4), server_default='0', nullable=False),
        sa.Column('projected_outflow', sa.Numeric(18, 4), server_default='0', nullable=False),
        sa.Column('projected_balance', sa.Numeric(18, 4), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_cashflow_forecast_lines_forecast_id', 'cashflow_forecast_lines', ['forecast_id'])
    op.create_index('ix_cashflow_forecast_lines_date', 'cashflow_forecast_lines', ['date'])


def downgrade():
    op.drop_table('cashflow_forecast_lines')
    op.drop_table('cashflow_forecasts')
