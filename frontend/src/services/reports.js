import api from './apiClient'

export const reportsAPI = {
    getSalesSummary: (start_date, end_date, branch_id) => api.get('/reports/sales/summary', { params: { start_date, end_date, branch_id } }),
    getSalesTrend: (days = 30, branch_id = null) => api.get('/reports/sales/trend', { params: { days, branch_id } }),
    getSalesByCustomer: (limit = 5, branch_id = null) => api.get('/reports/sales/by-customer', { params: { limit, branch_id } }),
    getSalesByProduct: (limit = 5, branch_id = null) => api.get('/reports/sales/by-product', { params: { limit, branch_id } }),
    getCustomerStatement: (customerId, params) => api.get(`/reports/sales/customer-statement/${customerId}`, { params }),
    getAgingReport: (branch_id = null) => api.get('/reports/sales/aging', { params: { branch_id } }),

    getPurchasesSummary: (params) => api.get('/reports/purchases/summary', { params }),
    getPurchasesTrend: (days = 30, branch_id = null) => api.get('/reports/purchases/trend', { params: { days, branch_id } }),
    getPurchasesBySupplier: (limit = 5, branch_id = null) => api.get('/reports/purchases/by-supplier', { params: { limit, branch_id } }),
    getSupplierStatement: (supplierId, params) => api.get(`/reports/purchases/supplier-statement/${supplierId}`, { params }),

    // HR Reports
    getPayrollTrend: (months = 12) => api.get('/reports/hr/payroll/trend', { params: { months } }),
    getLeaveUsage: (params) => api.get('/reports/hr/leaves/usage', { params }),

    // Financial Reports
    getGeneralLedger: (params) => api.get('/reports/accounting/general-ledger', { params }),
    getTrialBalance: (params) => api.get('/reports/accounting/trial-balance', { params }),
    getProfitLoss: (params) => api.get('/reports/accounting/profit-loss', { params }),
    getBalanceSheet: (params) => api.get('/reports/accounting/balance-sheet', { params }),
    getCashFlow: (params) => api.get('/reports/accounting/cashflow', { params }),
    getBudgetVsActual: (budgetId, params) => api.get(`/reports/accounting/budget-vs-actual`, { params: { budget_id: budgetId, ...params } }),

    // Period Comparison (ACC-004)
    compareProfitLoss: (params) => api.get('/reports/accounting/profit-loss/compare', { params }),
    compareBalanceSheet: (params) => api.get('/reports/accounting/balance-sheet/compare', { params }),
    compareTrialBalance: (params) => api.get('/reports/accounting/trial-balance/compare', { params }),
}

export const customReportsAPI = {
    create: (data) => api.post('/reports/custom', data),
    list: () => api.get('/reports/custom'),
    get: (id) => api.get(`/reports/custom/${id}`),
    delete: (id) => api.delete(`/reports/custom/${id}`),
    preview: (data) => api.post('/reports/custom/preview', data),
}

export const scheduledReportsAPI = {
    list: (params) => api.get('/reports/scheduled', { params }),
    create: (data) => api.post('/reports/scheduled', data),
    update: (id, data) => api.put(`/reports/scheduled/${id}`, data),
    delete: (id) => api.delete(`/reports/scheduled/${id}`),
    toggle: (id, active) => api.put(`/reports/scheduled/${id}/toggle`, null, { params: { active } })
}
