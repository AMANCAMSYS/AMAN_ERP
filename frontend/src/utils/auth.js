// Auth utilities

export function isAuthenticated() {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    const isAuth = !!token && !!user && user !== 'undefined' && user !== 'null';
    if (!isAuth && (token || user)) {
        console.log("auth: partial credentials found:", { hasToken: !!token, hasUser: !!user, userValue: user });
    }
    return isAuth;
}

export function getToken() {
    return localStorage.getItem('token')
}

// SEC-C4b: refresh token is kept in an HttpOnly, SameSite=Strict cookie
// issued by the backend (see utils/auth_cookies.py). It is NEVER written
// to localStorage anymore — that closed the XSS-→-token-theft path.
// This helper is kept only for compatibility; it always returns null.
export function getRefreshToken() {
    return null
}

export function getUser() {
    try {
        const user = localStorage.getItem('user')
        if (!user || user === 'undefined' || user === 'null') return null
        return JSON.parse(user)
    } catch (err) {
        console.error("Error parsing user from localStorage", err)
        localStorage.removeItem('user') // Clear corrupt data
        return null
    }
}

export function getCompanyId() {
    return localStorage.getItem('company_id')
}

export function getCurrency() {
    const user = getUser()
    return user?.currency || ''
}

export function getCountry() {
    const user = getUser()
    return user?.country || ''
}

// Permission aliases — mirrors backend PERMISSION_ALIASES
// If a user has the KEY permission, they implicitly have VALUE permissions
const PERMISSION_ALIASES = {
    'inventory.view':   ['stock.view', 'products.view'],
    'inventory.delete': ['products.delete', 'stock.adjustment'],
    'inventory.*':      ['stock.view', 'stock.view_cost', 'stock.adjustment', 'stock.transfer',
                         'stock.manage', 'stock.reports',
                         'products.view', 'products.create', 'products.edit', 'products.delete'],
    'projects.manage':  ['projects.view', 'projects.create', 'projects.edit', 'projects.delete'],
    'admin.users':      ['admin.roles', 'settings.view', 'settings.edit'],
    'admin.branches':   ['branches.view', 'branches.manage'],
    'sales.edit':       ['sales.create'],
    'sales.delete':     ['sales.create'],
    'buying.reports':   ['buying.view'],
    'hr.reports':       ['hr.view'],
    'reports.financial': ['reports.view'],
    'manufacturing.reports': ['manufacturing.view'],
    'notifications.send': ['notifications.view'],
    'finance.subscription_manage': ['finance.subscription_view'],
    'finance.cashflow_generate': ['finance.cashflow_view'],
    'crm.campaign_manage': ['crm.campaign_view'],
    'projects.resource_manage': ['projects.resource_view'],
    'projects.time_approve': ['projects.time_view'],
    'approvals.manage': ['approvals.view', 'approvals.create'],
    'accounting.manage': ['accounting.view', 'accounting.edit'],
    'treasury.manage': ['treasury.view', 'treasury.create', 'treasury.edit'],
    'taxes.manage': ['taxes.view'],
    'settings.manage': ['settings.view', 'settings.edit'],
}

export function hasPermission(permission) {
    const user = getUser()
    if (!user || !user.permissions || !Array.isArray(user.permissions)) {
        return false
    }

    // Admin check - wildcard for superuser
    if (user.permissions.includes('*')) return true

    // If permission is an array, check if user has ANY of them
    const requiredPermissions = Array.isArray(permission) ? permission : [permission]

    return requiredPermissions.some(perm => {
        if (!perm) return false
        // Exact match
        if (user.permissions.includes(perm)) return true

        // Check wildcard sections (e.g., 'sales.*')
        const parts = perm.split('.')
        if (parts.length > 1) {
            const sectionWildcard = parts[0] + '.*'
            if (user.permissions.includes(sectionWildcard)) return true
        }

        // Alias expansion: check if any user permission implies the required one
        for (const userPerm of user.permissions) {
            const implied = PERMISSION_ALIASES[userPerm]
            if (implied && implied.includes(perm)) return true
        }

        return false
    })
}

export function updateUser(userData) {
    const currentUser = getUser();
    const updatedUser = { ...currentUser, ...userData };
    localStorage.setItem('user', JSON.stringify(updatedUser));
}

export function setAuth(token, user, companyId, _refreshToken = null) {
    // SEC-C4b: refresh token is received as an HttpOnly cookie from /auth/login
    // and /auth/refresh. We deliberately do NOT persist it in localStorage.
    localStorage.setItem('token', token)
    // Purge any stale refresh_token written by older builds.
    localStorage.removeItem('refresh_token')
    localStorage.setItem('user', JSON.stringify(user))
    if (companyId) {
        localStorage.setItem('company_id', companyId)
    }
    // حفظ نوع النشاط التجاري أو مسحه (يضمن إعادة التوجيه للمعالج عند الشركات الجديدة)
    if (user?.industry_type) {
        localStorage.setItem('industry_type', user.industry_type)
    } else {
        // clear any stale value from a previous company login
        localStorage.removeItem('industry_type')
    }
}

export function clearAuth() {
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    localStorage.removeItem('company_id')
    localStorage.removeItem('industry_type')
}

export function logout() {
    clearAuth()
    window.location.href = '/login'
}
