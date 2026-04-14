"""Add campaign recipient and lead attribution tables, extend marketing_campaigns

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-13 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to existing marketing_campaigns table
    op.add_column('marketing_campaigns', sa.Column('segment_id', sa.Integer(),
                  sa.ForeignKey('crm_customer_segments.id', ondelete='SET NULL'), nullable=True))
    op.add_column('marketing_campaigns', sa.Column('subject', sa.String(500), nullable=True))
    op.add_column('marketing_campaigns', sa.Column('content', sa.Text(), nullable=True))
    op.add_column('marketing_campaigns', sa.Column('scheduled_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('marketing_campaigns', sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('marketing_campaigns', sa.Column('total_sent', sa.Integer(), server_default='0'))
    op.add_column('marketing_campaigns', sa.Column('total_delivered', sa.Integer(), server_default='0'))
    op.add_column('marketing_campaigns', sa.Column('total_opened', sa.Integer(), server_default='0'))
    op.add_column('marketing_campaigns', sa.Column('total_clicked', sa.Integer(), server_default='0'))
    op.add_column('marketing_campaigns', sa.Column('total_responded', sa.Integer(), server_default='0'))
    op.add_column('marketing_campaigns', sa.Column('estimated_cost', sa.Numeric(18, 4), server_default='0'))
    op.add_column('marketing_campaigns', sa.Column('actual_cost', sa.Numeric(18, 4), server_default='0'))

    op.create_index('ix_campaign_segment_id', 'marketing_campaigns', ['segment_id'])
    op.create_index('ix_campaign_status', 'marketing_campaigns', ['status'])

    # Create campaign_recipients table
    op.create_table(
        'campaign_recipients',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('campaign_id', sa.Integer(),
                  sa.ForeignKey('marketing_campaigns.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contact_id', sa.Integer(),
                  sa.ForeignKey('parties.id', ondelete='CASCADE'), nullable=False),
        sa.Column('channel', sa.String(10), server_default='email'),
        sa.Column('delivery_status', sa.String(20), server_default='pending'),
        sa.Column('opened_at', sa.DateTime(timezone=True)),
        sa.Column('clicked_at', sa.DateTime(timezone=True)),
        sa.Column('responded_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_campaign_recipient_campaign', 'campaign_recipients', ['campaign_id'])
    op.create_index('ix_campaign_recipient_contact', 'campaign_recipients', ['contact_id'])
    op.create_index('ix_campaign_recipient_status', 'campaign_recipients', ['delivery_status'])

    # Create campaign_lead_attributions table
    op.create_table(
        'campaign_lead_attributions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('campaign_id', sa.Integer(),
                  sa.ForeignKey('marketing_campaigns.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lead_id', sa.Integer(),
                  sa.ForeignKey('sales_opportunities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('attributed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_campaign_lead_attr_campaign', 'campaign_lead_attributions', ['campaign_id'])
    op.create_index('ix_campaign_lead_attr_lead', 'campaign_lead_attributions', ['lead_id'])


def downgrade() -> None:
    op.drop_table('campaign_lead_attributions')
    op.drop_table('campaign_recipients')

    op.drop_index('ix_campaign_status', table_name='marketing_campaigns')
    op.drop_index('ix_campaign_segment_id', table_name='marketing_campaigns')

    op.drop_column('marketing_campaigns', 'actual_cost')
    op.drop_column('marketing_campaigns', 'estimated_cost')
    op.drop_column('marketing_campaigns', 'total_responded')
    op.drop_column('marketing_campaigns', 'total_clicked')
    op.drop_column('marketing_campaigns', 'total_opened')
    op.drop_column('marketing_campaigns', 'total_delivered')
    op.drop_column('marketing_campaigns', 'total_sent')
    op.drop_column('marketing_campaigns', 'executed_at')
    op.drop_column('marketing_campaigns', 'scheduled_date')
    op.drop_column('marketing_campaigns', 'content')
    op.drop_column('marketing_campaigns', 'subject')
    op.drop_column('marketing_campaigns', 'segment_id')
