import api from './apiClient'

export const treasuryAPI = {
    listAccounts: (branchId) => api.get('/treasury/accounts', { params: { branch_id: branchId } }),
    createAccount: (data) => api.post('/treasury/accounts', data),
    updateAccount: (id, data) => api.put(`/treasury/accounts/${id}`, data),
    deleteAccount: (id) => api.delete(`/treasury/accounts/${id}`),
    createExpense: (data) => api.post('/treasury/transactions/expense', data),
    createTransfer: (data) => api.post('/treasury/transactions/transfer', data),
    listTransactions: (limit, branchId) => api.get('/treasury/transactions', { params: { limit, branch_id: branchId } }),

    // Treasury Reports
    getBalancesReport: (params) => api.get('/treasury/reports/balances', { params }),
    getCashflowReport: (params) => api.get('/treasury/reports/cashflow', { params }),

    // Bank Import
    importBankStatement: (file) => {
        const formData = new FormData();
        formData.append('file', file);
        return api.post('/treasury/bank-import', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    },
    listBankImports: () => api.get('/treasury/bank-import/batches'),
    getBankImportLines: (batchId) => api.get(`/treasury/bank-import/${batchId}/lines`),
    autoMatchBankImport: (batchId) => api.post(`/treasury/bank-import/${batchId}/auto-match`),
}

export const reconciliationAPI = {
    list: (params) => api.get('/reconciliation', { params }),
    get: (id) => api.get(`/reconciliation/${id}`),
    create: (data) => api.post('/reconciliation', data),
    addLines: (id, lines) => api.post(`/reconciliation/${id}/lines`, lines),
    deleteLine: (id, lineId) => api.delete(`/reconciliation/${id}/lines/${lineId}`),
    getLedger: (id) => api.get(`/reconciliation/${id}/ledger`),
    match: (id, data) => api.post(`/reconciliation/${id}/match`, data),
    unmatch: (id, data) => api.post(`/reconciliation/${id}/unmatch`, data),
    finalize: (id) => api.post(`/reconciliation/${id}/finalize`),
    delete: (id) => api.delete(`/reconciliation/${id}`),
    importPreview: (id, file) => {
        const formData = new FormData();
        formData.append('file', file);
        return api.post(`/reconciliation/${id}/import-preview`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    },
    importConfirm: (id, lines) => api.post(`/reconciliation/${id}/import-confirm`, lines),
    autoMatch: (id, toleranceDays = 3) => api.post(`/reconciliation/${id}/auto-match?tolerance_days=${toleranceDays}`),
}
