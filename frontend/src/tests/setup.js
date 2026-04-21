import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, vi } from 'vitest'

afterEach(() => {
    cleanup()
    localStorage.clear()
    sessionStorage.clear()
    vi.restoreAllMocks()
})

beforeEach(() => {
    // Ensure a predictable env for tests that read i18n cookies
    document.cookie = ''
})
