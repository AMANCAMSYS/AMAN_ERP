import { describe, it, expect, beforeEach } from 'vitest'
import {
    setAuth,
    clearAuth,
    getToken,
    getRefreshToken,
    getUser,
    isAuthenticated,
} from '../utils/auth'

describe('utils/auth', () => {
    beforeEach(() => localStorage.clear())

    it('setAuth stores access token in memory (NEVER localStorage) and never refresh token', () => {
        setAuth('access.jwt.value', { id: 1, username: 'u', permissions: [] }, 5, 'refresh.jwt.value')

        expect(getToken()).toBe('access.jwt.value')
        expect(getUser()).toMatchObject({ id: 1, username: 'u' })
        expect(localStorage.getItem('company_id')).toBe('5')

        // SEC-T2.8: access token must NOT be persisted to localStorage.
        expect(localStorage.getItem('token')).toBeNull()
        // SEC-C4b: refresh token must stay in the HttpOnly cookie, never in localStorage.
        expect(localStorage.getItem('refresh_token')).toBeNull()
        expect(getRefreshToken()).toBeNull()
    })

    it('setAuth purges any legacy token / refresh_token in localStorage', () => {
        localStorage.setItem('token', 'legacy.access')
        localStorage.setItem('refresh_token', 'legacy.value')
        setAuth('new.access', { id: 2, permissions: [] }, 1)
        expect(localStorage.getItem('token')).toBeNull()
        expect(localStorage.getItem('refresh_token')).toBeNull()
    })

    it('isAuthenticated is false without token, true with token + user', () => {
        expect(isAuthenticated()).toBe(false)
        setAuth('x', { id: 1, permissions: [] }, 1)
        expect(isAuthenticated()).toBe(true)
    })

    it('clearAuth removes everything', () => {
        setAuth('x', { id: 1, permissions: [] }, 1)
        clearAuth()
        expect(getToken()).toBeNull()
        expect(getUser()).toBeNull()
        expect(localStorage.getItem('company_id')).toBeNull()
    })
})
