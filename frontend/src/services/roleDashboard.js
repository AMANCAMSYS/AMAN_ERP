/**
 * Role-Based KPI Dashboard API Service
 * خدمة لوحات تحكم مؤشرات الأداء الوظيفية
 */
import api from './apiClient'

const BASE = '/dashboard/role'

export const roleDashboardAPI = {
    // Auto-detect dashboard by user role
    getAuto: (params) => api.get(`${BASE}/auto`, { params }),

    // Role-specific dashboards
    getExecutive: (params) => api.get(`${BASE}/executive`, { params }),
    getFinancial: (params) => api.get(`${BASE}/financial`, { params }),
    getSales: (params) => api.get(`${BASE}/sales`, { params }),
    getProcurement: (params) => api.get(`${BASE}/procurement`, { params }),
    getWarehouse: (params) => api.get(`${BASE}/warehouse`, { params }),
    getHR: (params) => api.get(`${BASE}/hr`, { params }),
    getManufacturing: (params) => api.get(`${BASE}/manufacturing`, { params }),
    getProjects: (params) => api.get(`${BASE}/projects`, { params }),
    getPOS: (params) => api.get(`${BASE}/pos`, { params }),
    getCRM: (params) => api.get(`${BASE}/crm`, { params }),

    // Industry KPIs (auto-detected)
    getIndustry: (params) => api.get(`${BASE}/industry`, { params }),

    // Combined (role + industry in one call)
    getCombined: (params) => api.get(`${BASE}/combined`, { params }),

    // List available dashboards for current user
    getAvailable: () => api.get(`${BASE}/available`),
}
