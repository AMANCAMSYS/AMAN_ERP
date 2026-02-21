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
        return false
    })
}

export function updateUser(userData) {
    const currentUser = getUser();
    const updatedUser = { ...currentUser, ...userData };
    localStorage.setItem('user', JSON.stringify(updatedUser));
}

export function setAuth(token, user, companyId) {
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(user))
    if (companyId) {
        localStorage.setItem('company_id', companyId)
    }
}

export function clearAuth() {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('company_id')
}

export function logout() {
    clearAuth()
    window.location.href = '/login'
}
