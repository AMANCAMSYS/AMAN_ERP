"""add cost layer tables

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-04-03
"""
from alembic import op
import sqlalchemy as sa

revision = 'e6f7a8b9c0d1'
down_revision = 'd5e6f7a8b9c0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'cost_layers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('warehouse_id', sa.Integer(), sa.ForeignKey('warehouses.id'), nullable=False),
        sa.Column('costing_method', sa.String(10), nullable=False),
        sa.Column('purchase_date', sa.Date(), nullable=False),
        sa.Column('original_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('remaining_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('unit_cost', sa.Numeric(18, 4), nullable=False),
        sa.Column('source_document_type', sa.String(30), nullable=False),
        sa.Column('source_document_id', sa.Integer(), nullable=True),
        sa.Column('is_exhausted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.CheckConstraint('remaining_quantity >= 0', name='ck_cost_layers_remaining_qty_non_negative'),
    )
    op.create_index(
        'ix_cost_layers_product_wh_exhausted_date',
        'cost_layers',
        ['product_id', 'warehouse_id', 'is_exhausted', 'purchase_date'],
    )

    op.create_table(
        'cost_layer_consumptions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('cost_layer_id', sa.Integer(), sa.ForeignKey('cost_layers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('quantity_consumed', sa.Numeric(18, 4), nullable=False),
        sa.Column('sale_document_type', sa.String(30), nullable=False),
        sa.Column('sale_document_id', sa.Integer(), nullable=True),
        sa.Column('consumed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('updated_by', sa.String(100), nullable=True),
    )
    op.create_index('ix_cost_layer_consumptions_layer_id', 'cost_layer_consumptions', ['cost_layer_id'])


def downgrade():
    op.drop_table('cost_layer_consumptions')
    op.drop_table('cost_layers')
