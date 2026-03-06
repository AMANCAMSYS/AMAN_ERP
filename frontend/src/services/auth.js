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
    logout: () => api.post('/auth/logout'),
    refresh: () => api.post('/auth/refresh'),
}
