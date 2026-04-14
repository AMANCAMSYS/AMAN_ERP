# Data Model: Authentication & Security Audit

**Feature**: `004-audit-auth-security`  
**Date**: 2026-04-14

## Existing Entities (Audit Scope)

> These entities already exist in the codebase. The audit validates their implementation against Constitution §IV requirements. No new tables are created.

### User (company_users table — per tenant DB)

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | INTEGER | PK, AUTO | |
| username | VARCHAR(100) | NOT NULL, UNIQUE | Used for login |
| email | VARCHAR(255) | | Used for password reset |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hash via passlib |
| full_name | VARCHAR(255) | | Display name |
| role | VARCHAR(50) | NOT NULL | References roles table |
| permissions | JSONB | | Array of `module.action` strings |
| allowed_branches | JSONB | | Array of branch IDs |
| enabled_modules | JSONB | | Array of module keys |
| is_active | BOOLEAN | DEFAULT TRUE | Checked on every sensitive operation |
| two_factor_enabled | BOOLEAN | DEFAULT FALSE | |
| last_login | TIMESTAMP | | |
| created_at | TIMESTAMP | DEFAULT NOW() | |

**Validation Rules**:
- Password must pass company password policy (min length, complexity, history)
- Username must be unique within tenant
- Role must exist in roles table

---

### Role (roles table — per tenant DB)

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | INTEGER | PK, AUTO | |
| name | VARCHAR(100) | NOT NULL, UNIQUE | e.g., admin, accountant |
| display_name | VARCHAR(255) | | Arabic display name |
| permissions | JSONB | NOT NULL | Array of permission strings |
| is_system | BOOLEAN | DEFAULT FALSE | Protects default roles from deletion |
| created_at | TIMESTAMP | DEFAULT NOW() | |

**State**: Static (no transitions). 12 default roles + custom roles.

---

### Token Blacklist (token_blacklist table — aman_system DB)

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | INTEGER | PK, AUTO | |
| token_hash | VARCHAR(64) | NOT NULL, INDEX | SHA-256 of token |
| expires_at | TIMESTAMP | NOT NULL | For cleanup |
| reason | VARCHAR(50) | | logout, password_change, admin_revoke |
| created_at | TIMESTAMP | DEFAULT NOW() | |

**Validation Rules**:
- Tokens stored as SHA-256 hashes (never plaintext)
- Automatic cleanup of expired entries

---

### User Session (user_sessions table — per tenant DB)

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | INTEGER | PK, AUTO | |
| user_id | INTEGER | FK → company_users | |
| token_hash | VARCHAR(64) | NOT NULL | SHA-256 of access token |
| ip_address | VARCHAR(45) | | IPv4/IPv6 |
| user_agent | VARCHAR(500) | | Browser/device info |
| created_at | TIMESTAMP | DEFAULT NOW() | |
| last_active | TIMESTAMP | | |
| is_active | BOOLEAN | DEFAULT TRUE | |

---

### Password History (password_history table — per tenant DB)

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | INTEGER | PK, AUTO | |
| user_id | INTEGER | FK → company_users | |
| password_hash | VARCHAR(255) | NOT NULL | Previous hash |
| created_at | TIMESTAMP | DEFAULT NOW() | |

**Validation Rules**:
- Checked against `prevent_reuse` policy setting (default: last N passwords)
- Only validated during password change operations

---

### 2FA Settings (user_2fa_settings table — per tenant DB)

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | INTEGER | PK, AUTO | |
| user_id | INTEGER | FK → company_users, UNIQUE | |
| totp_secret | VARCHAR(255) | NOT NULL | Encrypted TOTP secret |
| backup_codes | JSONB | | Array of SHA-256 hashed backup codes |
| is_active | BOOLEAN | DEFAULT FALSE | |
| created_at | TIMESTAMP | DEFAULT NOW() | |

---

### SSO Configuration (sso_configurations table — per tenant DB)

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | INTEGER | PK, AUTO | |
| provider_type | VARCHAR(20) | NOT NULL | saml, ldap |
| name | VARCHAR(255) | NOT NULL | Display name |
| is_active | BOOLEAN | DEFAULT TRUE | |
| metadata_url | TEXT | | SAML metadata URL |
| entity_id | VARCHAR(255) | | SAML entity ID |
| certificate | TEXT | | IdP X.509 certificate |
| ldap_host | VARCHAR(255) | | LDAP server |
| ldap_base_dn | VARCHAR(255) | | LDAP search base |
| ldap_bind_dn | VARCHAR(255) | | LDAP bind DN |
| created_at | TIMESTAMP | DEFAULT NOW() | |

---

### System User Index (system_user_index — aman_system DB)

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| username | VARCHAR(100) | PK | |
| company_id | VARCHAR(50) | NOT NULL | Routes to tenant DB |
| company_code | VARCHAR(20) | NOT NULL | Used in login |

**Validation Rules**:
- O(1) lookup for company routing during login
- No cross-tenant data in this table (only routing info)

---

## Entity Relationships

```
aman_system DB:
  system_user_index ──→ company routing
  token_blacklist    ──→ revoked tokens (cross-tenant)

aman_{company_id} DB:
  company_users ──┬──→ roles (via role name)
                  ├──→ user_sessions (1:N)
                  ├──→ password_history (1:N)
                  └──→ user_2fa_settings (1:1)
  
  sso_configurations ──→ sso_group_mappings (1:N)
```

## Audit-Specific Findings

### Tables Verified Present
- [x] company_users with proper fields
- [x] roles with permissions JSONB
- [x] token_blacklist in system DB
- [x] user_sessions for session tracking
- [x] password_history for reuse prevention
- [x] user_2fa_settings for TOTP
- [x] sso_configurations for SSO/LDAP
- [x] system_user_index for O(1) routing

### Data Integrity Checks Required
- Every `company_users.password_hash` must be bcrypt (no plaintext or weak hashes)
- `token_blacklist.token_hash` must be SHA-256 (not plaintext tokens)
- `user_2fa_settings.backup_codes` must be hashed (not plaintext)
- `sso_configurations` must not store LDAP bind passwords in plaintext
