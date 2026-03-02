import api from './apiClient'

export const assetsAPI = {
    list: (params) => api.get('/assets/', { params }),
    get: (id) => api.get(`/assets/${id}/`),
    create: (data) => api.post('/assets/', data),
    update: (id, data) => api.put(`/assets/${id}/`, data),
    dispose: (id, data) => api.post(`/assets/${id}/dispose`, data),
    postDepreciation: (assetId, scheduleId) => api.post(`/assets/${assetId}/depreciate/${scheduleId}/`),
    // Phase 8.14 - Advanced depreciation
    depreciationDecliningBalance: (id, data) => api.post(`/assets/${id}/depreciation/declining-balance`, data),
    depreciationUnitsOfProduction: (id, data) => api.post(`/assets/${id}/depreciation/units-of-production`, data),
    depreciationSumOfYears: (id, data) => api.post(`/assets/${id}/depreciation/sum-of-years`, data),
    // Asset Transfers
    listTransfers: (params) => api.get('/assets/transfers', { params }),
    createTransfer: (data) => api.post('/assets/transfers', data),
    approveTransfer: (id) => api.put(`/assets/transfers/${id}/approve`),
    // Revaluations
    listRevaluations: (params) => api.get('/assets/revaluations', { params }),
    createRevaluation: (data) => api.post('/assets/revaluations', data),
    // Insurance & Maintenance
    getInsurance: (id) => api.get(`/assets/${id}/insurance`),
    addInsurance: (id, data) => api.post(`/assets/${id}/insurance`, data),
    getMaintenance: (id) => api.get(`/assets/${id}/maintenance`),
    addMaintenance: (id, data) => api.post(`/assets/${id}/maintenance`, data),
    completeMaintenance: (id) => api.put(`/assets/maintenance/${id}/complete`),
    // QR / Barcode
    updateQR: (id, data) => api.put(`/assets/${id}/qr`, data),
    getQR: (id) => api.get(`/assets/${id}/qr`),

    // Individual Asset Revalue & Transfer (GL-003/GL-007)
    revalueAsset: (assetId, data) => api.post(`/assets/${assetId}/revalue`, data),
    transferAsset: (assetId, data) => api.post(`/assets/${assetId}/transfer`, data),

    // Reports
    getRegisterReport: (params) => api.get('/assets/reports/register', { params }),
    getDepreciationSummary: (params) => api.get('/assets/reports/depreciation-summary', { params }),
    getNetBookValueReport: (params) => api.get('/assets/reports/net-book-value', { params }),

    // IFRS 16 Lease Contracts (B6)
    listLeaseContracts: (params) => api.get('/assets/leases', { params }),
    createLeaseContract: (data) => api.post('/assets/leases', data),
    getLeaseSchedule: (leaseId) => api.get(`/assets/leases/${leaseId}/schedule`),

    // IAS 36 Impairment (B6)
    listImpairments: (assetId) => api.get(`/assets/${assetId}/impairments`),
    runImpairmentTest: (assetId, data) => api.post(`/assets/${assetId}/impairment-test`, data),
}
