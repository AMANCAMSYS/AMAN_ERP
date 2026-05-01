// SEC-T2.8 — In-memory access-token store.
//
// The access token used to live in localStorage, which made it readable by any
// XSS payload running in the page. We now keep it in a module-level closure so
// it can never be persisted or read from outside this module.
//
// The refresh token still lives in the HttpOnly cookie (see SEC-C4b); on full
// page reload the in-memory token is gone and `bootstrapAuth()` restores it
// silently by calling `/auth/refresh`. If that fails the user is logged out.
//
// DoD: after login, `localStorage.getItem('token')` MUST return null.

let inMemoryToken = null

export function getToken() {
    return inMemoryToken
}

export function setToken(token) {
    inMemoryToken = token || null
}

export function clearToken() {
    inMemoryToken = null
}

// Convenience: true if an access token is currently held in memory.
export function hasToken() {
    return !!inMemoryToken
}
