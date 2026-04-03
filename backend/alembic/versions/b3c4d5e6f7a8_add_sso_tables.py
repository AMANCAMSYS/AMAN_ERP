"""add sso tables

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-04-02

"""
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sso_configurations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider_type", sa.String(10), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("metadata_url", sa.String(1024), nullable=True),
        sa.Column("metadata_xml", sa.Text(), nullable=True),
        sa.Column("ldap_host", sa.String(255), nullable=True),
        sa.Column("ldap_port", sa.Integer(), nullable=True),
        sa.Column("ldap_base_dn", sa.String(512), nullable=True),
        sa.Column("ldap_bind_dn", sa.String(512), nullable=True),
        sa.Column("ldap_use_tls", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
    )

    op.create_table(
        "sso_group_role_mappings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sso_configuration_id", sa.Integer(), sa.ForeignKey("sso_configurations.id"), nullable=False),
        sa.Column("external_group_name", sa.String(255), nullable=False),
        sa.Column("aman_role_id", sa.Integer(), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
        sa.UniqueConstraint("sso_configuration_id", "external_group_name", name="uq_sso_group_mapping"),
    )

    op.create_table(
        "sso_fallback_admins",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sso_configuration_id", sa.Integer(), sa.ForeignKey("sso_configurations.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("company_users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("sso_fallback_admins")
    op.drop_table("sso_group_role_mappings")
    op.drop_table("sso_configurations")
