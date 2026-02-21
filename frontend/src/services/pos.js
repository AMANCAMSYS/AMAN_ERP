import api from './apiClient'

export const posAPI = {
    // Promotions
    listPromotions: (params) => api.get('/pos/promotions', { params }),
    createPromotion: (data) => api.post('/pos/promotions', data),
    updatePromotion: (id, data) => api.put(`/pos/promotions/${id}`, data),
    deletePromotion: (id) => api.delete(`/pos/promotions/${id}`),
    validateCoupon: (data) => api.post('/pos/promotions/validate', data),
    // Loyalty
    listLoyaltyPrograms: (params) => api.get('/pos/loyalty/programs', { params }),
    createLoyaltyProgram: (data) => api.post('/pos/loyalty/programs', data),
    getCustomerLoyalty: (partyId) => api.get(`/pos/loyalty/customer/${partyId}`),
    enrollLoyalty: (data) => api.post('/pos/loyalty/enroll', data),
    earnPoints: (data) => api.post('/pos/loyalty/earn', data),
    redeemPoints: (data) => api.post('/pos/loyalty/redeem', data),
    // Tables
    listTables: (params) => api.get('/pos/tables', { params }),
    createTable: (data) => api.post('/pos/tables', data),
    updateTable: (id, data) => api.put(`/pos/tables/${id}`, data),
    deleteTable: (id) => api.delete(`/pos/tables/${id}`),
    seatTable: (id, data) => api.post(`/pos/tables/${id}/seat`, data),
    clearTable: (id) => api.post(`/pos/tables/${id}/clear`),
    // Kitchen Display
    listKitchenOrders: (params) => api.get('/pos/kitchen/orders', { params }),
    createKitchenOrder: (data) => api.post('/pos/kitchen/orders', data),
    updateKitchenOrderStatus: (id, data) => api.put(`/pos/kitchen/orders/${id}/status`, data),
    // Session Reports
    getDetailedSessionReport: (sessionId) => api.get(`/pos/sessions/${sessionId}/detailed-report`),
}
