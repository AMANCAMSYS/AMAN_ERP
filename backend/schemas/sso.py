"""Pydantic schemas for SSO/LDAP configuration."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SsoConfigCreate(BaseModel):
    provider_type: str = Field(..., pattern="^(saml|ldap)$")
    display_name: str = Field(..., min_length=1, max_length=255)

    # SAML
    metadata_url: Optional[str] = None
    metadata_xml: Optional[str] = None

    # LDAP
    ldap_host: Optional[str] = None
    ldap_port: Optional[int] = None
    ldap_base_dn: Optional[str] = None
    ldap_bind_dn: Optional[str] = None
    ldap_use_tls: bool = True

    is_active: bool = False


class SsoConfigUpdate(BaseModel):
    display_name: Optional[str] = None
    metadata_url: Optional[str] = None
    metadata_xml: Optional[str] = None
    ldap_host: Optional[str] = None
    ldap_port: Optional[int] = None
    ldap_base_dn: Optional[str] = None
    ldap_bind_dn: Optional[str] = None
    ldap_use_tls: Optional[bool] = None
    is_active: Optional[bool] = None


class SsoConfigRead(BaseModel):
    id: int
    provider_type: str
    display_name: str
    metadata_url: Optional[str] = None
    ldap_host: Optional[str] = None
    ldap_port: Optional[int] = None
    ldap_base_dn: Optional[str] = None
    ldap_bind_dn: Optional[str] = None
    ldap_use_tls: bool = True
    is_active: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class GroupRoleMappingCreate(BaseModel):
    sso_configuration_id: int
    external_group_name: str = Field(..., min_length=1, max_length=255)
    aman_role_id: int


class GroupRoleMappingRead(BaseModel):
    id: int
    sso_configuration_id: int
    external_group_name: str
    aman_role_id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LdapTestRequest(BaseModel):
    ldap_host: str
    ldap_port: int = 636
    ldap_base_dn: str
    ldap_bind_dn: str
    ldap_bind_password: str
    ldap_use_tls: bool = True


class SamlMetadataResponse(BaseModel):
    entity_id: str
    acs_url: str
    metadata_xml: str


class SsoLoginRequest(BaseModel):
    sso_configuration_id: int
    company_id: Optional[str] = None
    # For LDAP direct login
    username: Optional[str] = None
    password: Optional[str] = None
