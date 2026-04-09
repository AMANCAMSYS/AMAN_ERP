import api from './apiClient'
import { cleanParams } from './apiClient'

export const subscriptionsAPI = {
    // Plans
    listPlans: (params) => api.get('/finance/subscriptions/plans', { params: cleanParams(params) }),
    createPlan: (data) => api.post('/finance/subscriptions/plans', data),
    updatePlan: (id, data) => api.put(`/finance/subscriptions/plans/${id}`, data),

    // Enrollments
    enroll: (data) => api.post('/finance/subscriptions/enroll', data),
    listEnrollments: (params) => api.get('/finance/subscriptions/enrollments', { params: cleanParams(params) }),
    getEnrollment: (id) => api.get(`/finance/subscriptions/enrollments/${id}`),
    pauseEnrollment: (id) => api.post(`/finance/subscriptions/enrollments/${id}/pause`),
    resumeEnrollment: (id) => api.post(`/finance/subscriptions/enrollments/${id}/resume`),
    cancelEnrollment: (id, data) => api.post(`/finance/subscriptions/enrollments/${id}/cancel`, data),
    changePlan: (id, data) => api.post(`/finance/subscriptions/enrollments/${id}/change-plan`, data),
}
