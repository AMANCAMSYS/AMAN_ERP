# API Contracts: Authentication & Security

**Feature**: `004-audit-auth-security`  
**Date**: 2026-04-14

## Authentication Endpoints

### POST /auth/login
**Access**: Public  
**Rate Limit**: 5 attempts/min per IP, 15-min lockout

**Request**:
```json
{
  "username": "string (required)",
  "password": "string (required)",
  "company_code": "string (optional, from form or header)"
}
```

**Response 200**:
```json
{
  "access_token": "string (JWT, 30-min expiry)",
  "refresh_token": "string (JWT, 7-day expiry)",
  "token_type": "bearer",
  "user": {
    "id": "integer",
    "username": "string",
    "full_name": "string",
    "email": "string",
    "role": "string",
    "permissions": ["module.action", ...],
    "enabled_modules": ["module_key", ...],
    "allowed_branches": [1, 2, ...],
    "two_factor_enabled": "boolean",
    "company_id": "string"
  }
}
```

**Response 200 (2FA required)**:
```json
{
  "requires_2fa": true,
  "temp_token": "string (short-lived token for 2FA verification)"
}
```

**Response 401**: `{"detail": "بيانات تسجيل الدخول غير صحيحة"}`  
**Response 429**: `{"detail": "تم تجاوز عدد المحاولات المسموح بها"}`

**Security Contract**:
- MUST NOT return different errors for invalid username vs invalid password
- MUST hash token before storing in user_sessions
- MUST log failed attempts with IP (never password)
- MUST check token blacklist and user active status

---

### POST /auth/logout
**Access**: Authenticated  
**Headers**: `Authorization: Bearer <access_token>`

**Response 200**:
```json
{
  "message": "تم تسجيل الخروج بنجاح"
}
```

**Security Contract**:
- MUST blacklist both access and refresh tokens
- MUST update token_blacklist in DB AND Redis cache
- MUST invalidate the user_session record

---

### POST /auth/refresh
**Access**: Refresh token only  
**Rate Limit**: General API limit

**Request**:
```json
{
  "refresh_token": "string (required)"
}
```

**Response 200**:
```json
{
  "access_token": "string (new JWT, 30-min expiry)",
  "token_type": "bearer"
}
```

**Response 401**: Expired or blacklisted refresh token

**Security Contract**:
- MUST verify refresh token is not blacklisted
- MUST verify token type is "refresh"
- MUST verify user is still active in DB

---

### POST /auth/forgot-password
**Access**: Public  
**Rate Limit**: 3 attempts/min per email

**Request**:
```json
{
  "email": "string (required)"
}
```

**Response 200**: `{"message": "تم إرسال رابط إعادة التعيين"}` (always, even if email not found)

**Security Contract**:
- MUST NOT reveal whether email exists in system
- MUST generate single-use reset token

---

## Security Endpoints

### POST /security/2fa/setup
**Access**: Authenticated (own account)

**Response 200**:
```json
{
  "secret": "string (TOTP base32 secret)",
  "qr_code": "string (base64 QR image)",
  "backup_codes": ["string", ...] 
}
```

**Security Contract**:
- Backup codes MUST be shown only once
- Backup codes MUST be stored as SHA-256 hashes

---

### POST /security/change-password
**Access**: Authenticated (own account)

**Request**:
```json
{
  "current_password": "string (required)",
  "new_password": "string (required)"
}
```

**Response 200**: `{"message": "تم تغيير كلمة المرور بنجاح"}`

**Security Contract**:
- MUST validate against password policy (min length, complexity)
- MUST check password history (prevent reuse)
- MUST invalidate all active tokens after password change
- Token invalidation MUST NOT be wrapped in try-except with silent failure

---

### GET /security/sessions
**Access**: Authenticated (own account)

**Response 200**:
```json
{
  "sessions": [
    {
      "id": "integer",
      "ip_address": "string",
      "user_agent": "string",
      "created_at": "datetime",
      "last_active": "datetime",
      "is_current": "boolean"
    }
  ]
}
```

---

### GET /security/events
**Access**: Authenticated, requires `security.view` permission

**Query Params**: `page`, `per_page`, `event_type`, `user_id`, `date_from`, `date_to`

**Response 200**:
```json
{
  "items": [
    {
      "id": "integer",
      "event_type": "string",
      "user_id": "integer",
      "username": "string",
      "ip_address": "string",
      "details": "string",
      "created_at": "datetime"
    }
  ],
  "total": "integer",
  "page": "integer",
  "per_page": "integer"
}
```

---

## SSO Endpoints

### POST /sso/saml/acs
**Access**: Public (SAML callback from IdP)

**Security Contract**:
- MUST validate SAML response signature against IdP certificate
- MUST validate response timestamp (prevent replay)
- MUST use server-side state for RelayState (NOT user-controllable company_id)
- MUST log all SSO login attempts

---

## Error Response Contract

All error responses MUST follow this pattern:

```json
{
  "detail": "string (user-friendly Arabic message, NEVER raw exception)"
}
```

**Forbidden patterns** (Constitution §IV violation):
- `raise HTTPException(detail=str(e))` 
- `raise HTTPException(detail=f"Error: {traceback}")`
- Any response containing Python class names, file paths, or SQL errors
