"""add blanket purchase order tables

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-13 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'blanket_purchase_orders',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('supplier_id', sa.Integer(), sa.ForeignKey('parties.id'), nullable=False),
        sa.Column('agreement_number', sa.String(50), nullable=False, unique=True),
        sa.Column('total_quantity', sa.Numeric(18, 4), server_default='0'),
        sa.Column('unit_price', sa.Numeric(18, 4), server_default='0'),
        sa.Column('total_amount', sa.Numeric(18, 4), server_default='0'),
        sa.Column('released_quantity', sa.Numeric(18, 4), server_default='0'),
        sa.Column('released_amount', sa.Numeric(18, 4), server_default='0'),
        sa.Column('valid_from', sa.Date()),
        sa.Column('valid_to', sa.Date()),
        sa.Column('status', sa.String(20), server_default='draft'),
        sa.Column('price_amendment_history', JSONB, server_default='[]'),
        sa.Column('branch_id', sa.Integer(), sa.ForeignKey('branches.id')),
        sa.Column('currency', sa.String(3), server_default='SAR'),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', sa.String(100)),
        sa.Column('updated_by', sa.String(100)),
    )

    op.create_table(
        'blanket_po_release_orders',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('blanket_po_id', sa.Integer(), sa.ForeignKey('blanket_purchase_orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('purchase_order_id', sa.Integer(), sa.ForeignKey('purchase_orders.id')),
        sa.Column('release_quantity', sa.Numeric(18, 4), server_default='0'),
        sa.Column('release_amount', sa.Numeric(18, 4), server_default='0'),
        sa.Column('release_date', sa.Date()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', sa.String(100)),
        sa.Column('updated_by', sa.String(100)),
    )

    op.create_index('ix_blanket_po_supplier', 'blanket_purchase_orders', ['supplier_id'])
    op.create_index('ix_blanket_po_status', 'blanket_purchase_orders', ['status'])
    op.create_index('ix_blanket_po_release_bpo', 'blanket_po_release_orders', ['blanket_po_id'])


def downgrade() -> None:
    op.drop_index('ix_blanket_po_release_bpo', 'blanket_po_release_orders')
    op.drop_index('ix_blanket_po_status', 'blanket_purchase_orders')
    op.drop_index('ix_blanket_po_supplier', 'blanket_purchase_orders')
    op.drop_table('blanket_po_release_orders')
    op.drop_table('blanket_purchase_orders')
