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
    getSsoProviders: (companyCode) =>
        api.get('/auth/sso/providers', { params: { company_code: companyCode } }),
    ssoLogin: (ssoConfigurationId, companyCode, username, password) =>
        api.post('/auth/sso/login', {
            sso_configuration_id: ssoConfigurationId,
            company_code: companyCode,
            username,
            password,
        }),
    verify2FALogin: (temp_token, code) =>
        api.post('/auth/2fa/verify-login', { temp_token, code }),
}
