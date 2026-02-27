import api from './apiClient'

export const authAPI = {
    login: (username, password) => {
        const formData = new URLSearchParams()
        formData.append('username', username)
        formData.append('password', password)
        return api.post('/auth/login', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })
    },
    me: () => api.get('/auth/me'),
    logout: () => api.post('/auth/logout'),
    refresh: () => api.post('/auth/refresh'),
}
