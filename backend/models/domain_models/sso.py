"""SSO/LDAP configuration models."""

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..base import AuditMixin, ModelBase, SoftDeleteMixin


class SsoConfiguration(ModelBase, AuditMixin, SoftDeleteMixin):
    """SSO provider configuration (SAML or LDAP)."""
    __tablename__ = "sso_configurations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider_type: Mapped[str] = mapped_column(String(10), nullable=False)  # "saml" or "ldap"
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # SAML fields
    metadata_url: Mapped[str | None] = mapped_column(String(1024))
    metadata_xml: Mapped[str | None] = mapped_column(Text)

    # LDAP fields
    ldap_host: Mapped[str | None] = mapped_column(String(255))
    ldap_port: Mapped[int | None] = mapped_column(Integer)
    ldap_base_dn: Mapped[str | None] = mapped_column(String(512))
    ldap_bind_dn: Mapped[str | None] = mapped_column(String(512))
    ldap_use_tls: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    is_active: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


class SsoGroupRoleMapping(ModelBase, AuditMixin, SoftDeleteMixin):
    """Maps external IdP group names to AMAN roles."""
    __tablename__ = "sso_group_role_mappings"
    __table_args__ = (
        UniqueConstraint("sso_configuration_id", "external_group_name", name="uq_sso_group_mapping"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sso_configuration_id: Mapped[int] = mapped_column(Integer, ForeignKey("sso_configurations.id", ondelete="CASCADE"), nullable=False)
    external_group_name: Mapped[str] = mapped_column(String(255), nullable=False)
    aman_role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)


class SsoFallbackAdmin(ModelBase, AuditMixin, SoftDeleteMixin):
    """Designates users who can log in locally when the IdP is unreachable."""
    __tablename__ = "sso_fallback_admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sso_configuration_id: Mapped[int] = mapped_column(Integer, ForeignKey("sso_configurations.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("company_users.id", ondelete="CASCADE"), nullable=False)
