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
    convertToQuotation: (oppId) => api.post(`/crm/opportunities/${oppId}/convert-quotation`),
    // Marketing Campaigns
    listCampaigns: (params) => api.get('/crm/campaigns', { params }),
    getCampaign: (id) => api.get(`/crm/campaigns/${id}`),
    createCampaign: (data) => api.post('/crm/campaigns', data),
    updateCampaign: (id, data) => api.put(`/crm/campaigns/${id}`, data),
    deleteCampaign: (id) => api.delete(`/crm/campaigns/${id}`),
    // Knowledge Base
    listArticles: (params) => api.get('/crm/knowledge-base', { params }),
    getArticle: (id) => api.get(`/crm/knowledge-base/${id}`),
    createArticle: (data) => api.post('/crm/knowledge-base', data),
    updateArticle: (id, data) => api.put(`/crm/knowledge-base/${id}`, data),
    deleteArticle: (id) => api.delete(`/crm/knowledge-base/${id}`),
    // Support Tickets
    listTickets: (params) => api.get('/crm/tickets', { params }),
    getTicketStats: () => api.get('/crm/tickets/stats'),
    getTicket: (id) => api.get(`/crm/tickets/${id}`),
    createTicket: (data) => api.post('/crm/tickets', data),
    updateTicket: (id, data) => api.put(`/crm/tickets/${id}`, data),
    addComment: (ticketId, data) => api.post(`/crm/tickets/${ticketId}/comments`, data),
}
