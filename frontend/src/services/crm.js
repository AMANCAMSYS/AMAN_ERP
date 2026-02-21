import api from './apiClient'

export const crmAPI = {
    // Opportunities
    listOpportunities: (params) => api.get('/crm/opportunities', { params }),
    getPipelineSummary: () => api.get('/crm/opportunities/pipeline'),
    getOpportunity: (id) => api.get(`/crm/opportunities/${id}`),
    createOpportunity: (data) => api.post('/crm/opportunities', data),
    updateOpportunity: (id, data) => api.put(`/crm/opportunities/${id}`, data),
    deleteOpportunity: (id) => api.delete(`/crm/opportunities/${id}`),
    addActivity: (oppId, data) => api.post(`/crm/opportunities/${oppId}/activities`, data),
    // Support Tickets
    listTickets: (params) => api.get('/crm/tickets', { params }),
    getTicketStats: () => api.get('/crm/tickets/stats'),
    getTicket: (id) => api.get(`/crm/tickets/${id}`),
    createTicket: (data) => api.post('/crm/tickets', data),
    updateTicket: (id, data) => api.put(`/crm/tickets/${id}`, data),
    addComment: (ticketId, data) => api.post(`/crm/tickets/${ticketId}/comments`, data),
}
