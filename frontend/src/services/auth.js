import api from './apiClient'

export const authAPI = {
    login: (username, password, companyCode) => {
        const formData = new URLSearchParams()
        formData.append('username', username)
        formData.append('password', password)
        if (companyCode) {
            formData.append('company_code', companyCode.trim())
        }
        return api.post('/auth/login', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })
    },
    me: () => api.get('/auth/me'),
    updateMe: (data) => api.put('/auth/me', data),
    logout: () => {
        const refreshToken = localStorage.getItem('refresh_token')
        return api.post('/auth/logout', refreshToken ? { refresh_token: refreshToken } : {})
    },
    refresh: () => {
        const refreshToken = localStorage.getItem('refresh_token')
        return api.post('/auth/refresh', { refresh_token: refreshToken })
    },
}
