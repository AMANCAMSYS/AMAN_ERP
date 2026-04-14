"""add cpq tables

Revision ID: g2h3i4j5k6l7
Revises: f1a2b3c4d5e6
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = 'g2h3i4j5k6l7'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ProductConfiguration
    op.create_table(
        'product_configurations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_prod_config_product', 'product_configurations', ['product_id'])

    # ConfigOptionGroup
    op.create_table(
        'config_option_groups',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('configuration_id', sa.Integer(), sa.ForeignKey('product_configurations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('is_required', sa.Boolean(), server_default='true'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_config_group_config', 'config_option_groups', ['configuration_id'])

    # ConfigOption
    op.create_table(
        'config_options',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('group_id', sa.Integer(), sa.ForeignKey('config_option_groups.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('price_adjustment', sa.Numeric(18, 4), server_default='0'),
        sa.Column('is_default', sa.Boolean(), server_default='false'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_config_option_group', 'config_options', ['group_id'])

    # ConfigValidationRule
    op.create_table(
        'config_validation_rules',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('configuration_id', sa.Integer(), sa.ForeignKey('product_configurations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rule_type', sa.String(20), nullable=False),
        sa.Column('source_option_id', sa.Integer(), sa.ForeignKey('config_options.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_option_id', sa.Integer(), sa.ForeignKey('config_options.id', ondelete='CASCADE'), nullable=False),
        sa.Column('error_message', sa.String(500)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_validation_rule_config', 'config_validation_rules', ['configuration_id'])

    # CpqPricingRule
    op.create_table(
        'cpq_pricing_rules',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('configuration_id', sa.Integer(), sa.ForeignKey('product_configurations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rule_type', sa.String(30), nullable=False),
        sa.Column('min_quantity', sa.Integer()),
        sa.Column('max_quantity', sa.Integer()),
        sa.Column('discount_percent', sa.Numeric(5, 2)),
        sa.Column('discount_amount', sa.Numeric(18, 4)),
        sa.Column('customer_group_id', sa.Integer(), sa.ForeignKey('party_groups.id', ondelete='SET NULL')),
        sa.Column('priority', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_pricing_rule_config', 'cpq_pricing_rules', ['configuration_id'])

    # CpqQuote
    op.create_table(
        'cpq_quotes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('parties.id'), nullable=False),
        sa.Column('quotation_id', sa.Integer(), sa.ForeignKey('sales_quotations.id', ondelete='SET NULL')),
        sa.Column('total_amount', sa.Numeric(18, 4), server_default='0'),
        sa.Column('discount_total', sa.Numeric(18, 4), server_default='0'),
        sa.Column('final_amount', sa.Numeric(18, 4), server_default='0'),
        sa.Column('pdf_path', sa.String(500)),
        sa.Column('status', sa.String(20), server_default="'draft'"),
        sa.Column('valid_until', sa.Date()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_cpq_quote_customer', 'cpq_quotes', ['customer_id'])

    # CpqQuoteLine
    op.create_table(
        'cpq_quote_lines',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('quote_id', sa.Integer(), sa.ForeignKey('cpq_quotes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('selected_options', JSONB),
        sa.Column('quantity', sa.Numeric(18, 4), server_default='1'),
        sa.Column('base_unit_price', sa.Numeric(18, 4), server_default='0'),
        sa.Column('option_adjustments', sa.Numeric(18, 4), server_default='0'),
        sa.Column('discount_applied', sa.Numeric(18, 4), server_default='0'),
        sa.Column('final_unit_price', sa.Numeric(18, 4), server_default='0'),
        sa.Column('line_total', sa.Numeric(18, 4), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_cpq_line_quote', 'cpq_quote_lines', ['quote_id'])


def downgrade() -> None:
    op.drop_table('cpq_quote_lines')
    op.drop_table('cpq_quotes')
    op.drop_table('cpq_pricing_rules')
    op.drop_table('config_validation_rules')
    op.drop_table('config_options')
    op.drop_table('config_option_groups')
    op.drop_table('product_configurations')
