import api from './apiClient'

export const purchasesAPI = {
    createInvoice: (data) => api.post('/buying/invoices', data),
    listInvoices: (params) => api.get('/buying/invoices', { params }),
    getInvoice: (id) => api.get(`/buying/invoices/${id}`),

    // Purchase Orders
    listOrders: (params) => api.get('/buying/orders', { params }),
    getOrder: (id) => api.get(`/buying/orders/${id}`),
    createOrder: (data) => api.post('/buying/orders', data),
    approveOrder: (id) => api.put(`/buying/orders/${id}/approve`),
    receiveOrder: (id, data) => api.post(`/buying/orders/${id}/receive`, data),

    // Supplier Groups
    listSupplierGroups: (params) => api.get('/buying/supplier-groups', { params }),
    createSupplierGroup: (data) => api.post('/buying/supplier-groups', data),
    updateSupplierGroup: (id, data) => api.put(`/buying/supplier-groups/${id}`, data),
    deleteSupplierGroup: (id) => api.delete(`/buying/supplier-groups/${id}`),

    // Supplier Payments
    createPayment: (data) => api.post('/buying/payments', data),
    listPayments: (params) => api.get('/buying/payments', { params }),
    getPayment: (id) => api.get(`/buying/payments/${id}`),
    getOutstandingInvoices: (supplierId, params) => api.get(`/buying/suppliers/${supplierId}/outstanding-invoices`, { params }),
    getInvoicePaymentHistory: (invoiceId) => api.get(`/buying/invoices/${invoiceId}/payment-history`),
    getSupplierTransactions: (supplierId, branchId) => api.get(`/buying/suppliers/${supplierId}/transactions`, { params: { branch_id: branchId } }),

    // Purchase Returns
    listReturns: (params) => api.get('/buying/returns', { params }),
    createReturn: (data) => api.post('/buying/returns', data),
    getReturn: (id) => api.get(`/buying/returns/${id}`),

    // Purchase Credit Notes
    listCreditNotes: (params) => api.get('/buying/credit-notes', { params }),
    getCreditNote: (id) => api.get(`/buying/credit-notes/${id}`),
    createCreditNote: (data) => api.post('/buying/credit-notes', data),

    // Purchase Debit Notes
    listDebitNotes: (params) => api.get('/buying/debit-notes', { params }),
    getDebitNote: (id) => api.get(`/buying/debit-notes/${id}`),
    createDebitNote: (data) => api.post('/buying/debit-notes', data),

    getSummary: (params) => api.get('/buying/summary', { params }),

    // Phase 8.11 - Purchases Improvements
    // RFQ
    listRFQs: (params) => api.get('/buying/rfq', { params }),
    getRFQ: (id) => api.get(`/buying/rfq/${id}`),
    createRFQ: (data) => api.post('/buying/rfq', data),
    sendRFQ: (id) => api.put(`/buying/rfq/${id}/send`),
    addRFQResponse: (id, data) => api.post(`/buying/rfq/${id}/responses`, data),
    compareRFQ: (id) => api.post(`/buying/rfq/${id}/compare`),
    convertRFQtoPO: (id, data) => api.post(`/buying/rfq/${id}/convert`, data),
    // Supplier Ratings
    listSupplierRatings: (params) => api.get('/buying/supplier-ratings', { params }),
    getSupplierRatingSummary: (supplierId) => api.get(`/buying/supplier-ratings/summary/${supplierId}`),
    createSupplierRating: (data) => api.post('/buying/supplier-ratings', data),
    // Purchase Agreements
    listAgreements: (params) => api.get('/buying/agreements', { params }),
    getAgreement: (id) => api.get(`/buying/agreements/${id}`),
    createAgreement: (data) => api.post('/buying/agreements', data),
    activateAgreement: (id) => api.put(`/buying/agreements/${id}/activate`),
    callOffAgreement: (id, data) => api.post(`/buying/agreements/${id}/call-off`, data),
}
