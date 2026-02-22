import api from './apiClient'

export const manufacturingAPI = {
    // Work Centers
    listWorkCenters: () => api.get('/manufacturing/work-centers'),
    createWorkCenter: (data) => api.post('/manufacturing/work-centers', data),
    updateWorkCenter: (id, data) => api.put(`/manufacturing/work-centers/${id}`, data),
    deleteWorkCenter: (id) => api.delete(`/manufacturing/work-centers/${id}`),

    // Routings
    listRoutes: () => api.get('/manufacturing/routes'),
    createRoute: (data) => api.post('/manufacturing/routes', data),
    updateRoute: (id, data) => api.put(`/manufacturing/routes/${id}`, data),
    deleteRoute: (id) => api.delete(`/manufacturing/routes/${id}`),

    // BOMs
    listBOMs: () => api.get('/manufacturing/boms'),
    createBOM: (data) => api.post('/manufacturing/boms', data),
    getBOM: (id) => api.get(`/manufacturing/boms/${id}`),
    updateBOM: (id, data) => api.put(`/manufacturing/boms/${id}`, data),
    deleteBOM: (id) => api.delete(`/manufacturing/boms/${id}`),

    // Operations (Scheduling)
    listOperations: (params) => api.get('/manufacturing/operations', { params }),

    // Orders
    listOrders: (params) => api.get('/manufacturing/orders', { params }),
    getOrder: (id) => api.get(`/manufacturing/orders/${id}`),
    createOrder: (data) => api.post('/manufacturing/orders', data),
    completeOrder: (id) => api.post(`/manufacturing/orders/${id}/complete`),
    startOrder: (id) => api.post(`/manufacturing/orders/${id}/start`),
    cancelOrder: (id) => api.post(`/manufacturing/orders/${id}/cancel`),
    getDashboardStats: () => api.get('/manufacturing/dashboard/stats'),

    // Equipment
    listEquipment: () => api.get('/manufacturing/equipment'),
    createEquipment: (data) => api.post('/manufacturing/equipment', data),

    // Maintenance
    listMaintenanceLogs: (params) => api.get('/manufacturing/maintenance-logs', { params }),
    createMaintenanceLog: (data) => api.post('/manufacturing/maintenance-logs', data),

    // Reports
    getDirectLaborReport: (params) => api.get('/manufacturing/reports/direct-labor', { params }),
    getProductionCostReport: (params) => api.get('/manufacturing/reports/production-cost', { params }),
    getWorkCenterEfficiency: (params) => api.get('/manufacturing/reports/work-center-efficiency', { params }),
    getProductionSummary: (params) => api.get('/manufacturing/reports/production-summary', { params })
}
