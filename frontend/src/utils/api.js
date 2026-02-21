import axios from 'axios'
import { toastEmitter } from './toastEmitter'

const api = axios.create({
    baseURL: '/api',
    headers: {
        'Content-Type': 'application/json'
    }
})

// Add auth token to requests
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// Handle API errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        // Option to skip global toast for specific requests
        const skipToast = error.config?.skipGlobalToast;

        if (error.response?.status === 401) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            localStorage.removeItem('company_id');
            window.location.href = '/login';
        } else if (!skipToast && error.response) {
            const status = error.response.status;
            const detail = error.response.data?.detail;
            const lang = localStorage.getItem('i18nextLng') || 'ar';

            let message = '';
            let type = 'error';

            if (status === 403) {
                message = lang === 'ar'
                    ? 'ليس لديك صلاحية للقيام بهذا الإجراء'
                    : 'You do not have permission to perform this action';
                type = 'warning';
            } else if (status >= 400 && status < 500) {
                // Client error - show detail if it's a string, otherwise default
                if (typeof detail === 'string') {
                    message = detail;
                } else if (Array.isArray(detail)) {
                    // FastAPI validation errors
                    message = detail.map(d => d.msg).join(', ');
                } else {
                    message = lang === 'ar'
                        ? 'يرجى مراجعة البيانات المدخلة'
                        : 'Please check your input';
                }
            } else if (status >= 500) {
                // Server error
                message = lang === 'ar'
                    ? 'حدث خطأ في النظام، يرجى المحاولة لاحقاً'
                    : 'A system error occurred, please try again later';
            }

            if (message) {
                toastEmitter.emit(message, type);
            }
        }
        return Promise.reject(error);
    }
);


// Auth API
export const authAPI = {
    login: (username, password) => {
        const formData = new URLSearchParams()
        formData.append('username', username)
        formData.append('password', password)
        return api.post('/auth/login', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })
    },
    me: () => api.get('/auth/me'),
    logout: () => api.post('/auth/logout')
}

// Companies API
export const companiesAPI = {
    register: (data) => api.post('/companies/register', data),
    list: (params) => api.get('/companies/list', { params }),
    get: (id) => api.get(`/companies/${id}`),
    // Helper to get current company info using the company_id from local storage
    getCurrentCompany: (companyId) => api.get(`/companies/${companyId}`)
}

// Reports API
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

// Accounting API
export const accountingAPI = {
    list: (params) => api.get('/accounting/accounts', { params }),
    create: (data) => api.post('/accounting/accounts', data),
    update: (id, data) => api.put(`/accounting/accounts/${id}`, data),
    delete: (id) => api.delete(`/accounting/accounts/${id}`),
    createJournalEntry: (data) => api.post('/accounting/journal-entries', data),
    voidJournalEntry: (id) => api.post(`/accounting/journal-entries/${id}/void`),
    getSummary: (params) => api.get('/accounting/summary', { params }),

    // Fiscal Years (ACC-001)
    listFiscalYears: () => api.get('/accounting/fiscal-years'),
    createFiscalYear: (data) => api.post('/accounting/fiscal-years', data),
    previewClosing: (year) => api.get(`/accounting/fiscal-years/${year}/preview-closing`),
    closeFiscalYear: (year, data) => api.post(`/accounting/fiscal-years/${year}/close`, data),
    reopenFiscalYear: (year, data) => api.post(`/accounting/fiscal-years/${year}/reopen`, data),
    listFiscalPeriods: (year) => api.get(`/accounting/fiscal-years/${year}/periods`),
    togglePeriod: (periodId) => api.post(`/accounting/fiscal-periods/${periodId}/toggle-close`),

    // Journal Entries (ACC-002)
    listJournalEntries: (params) => api.get('/accounting/journal-entries', { params }),
    getJournalEntry: (id) => api.get(`/accounting/journal-entries/${id}`),
    postJournalEntry: (id) => api.post(`/accounting/journal-entries/${id}/post`),

    // Recurring Templates (ACC-003)
    listRecurringTemplates: (params) => api.get('/accounting/recurring-templates', { params }),
    getRecurringTemplate: (id) => api.get(`/accounting/recurring-templates/${id}`),
    createRecurringTemplate: (data) => api.post('/accounting/recurring-templates', data),
    updateRecurringTemplate: (id, data) => api.put(`/accounting/recurring-templates/${id}`, data),
    deleteRecurringTemplate: (id) => api.delete(`/accounting/recurring-templates/${id}`),
    generateFromTemplate: (id) => api.post(`/accounting/recurring-templates/${id}/generate`),
    generateDueTemplates: () => api.post('/accounting/recurring-templates/generate-due'),

    // Opening Balances (ACC-005)
    getOpeningBalances: () => api.get('/accounting/opening-balances'),
    saveOpeningBalances: (data) => api.post('/accounting/opening-balances', data),

    // Closing Entries (ACC-006)
    previewClosingEntries: (params) => api.get('/accounting/closing-entries/preview', { params }),
    generateClosingEntries: (data) => api.post('/accounting/closing-entries/generate', data),
}

export const costCentersAPI = {
    list: () => api.get('/cost-centers/'),
    create: (data) => api.post('/cost-centers/', data),
    update: (id, data) => api.put(`/cost-centers/${id}`, data),
    delete: (id) => api.delete(`/cost-centers/${id}`)
}

// Budgets API
export const budgetsAPI = {
    list: () => api.get('/accounting/budgets/'),
    create: (data) => api.post('/accounting/budgets/', data),
    get: (id) => api.get(`/accounting/budgets/${id}`),
    update: (id, data) => api.put(`/accounting/budgets/${id}`, data),
    setItems: (id, items) => api.post(`/accounting/budgets/${id}/items`, items),
    getItems: (id) => api.get(`/accounting/budgets/${id}/items`),
    getReport: (id, params) => api.get(`/accounting/budgets/${id}/report`, { params }),
    delete: (id) => api.delete(`/accounting/budgets/${id}`),
    activate: (id) => api.post(`/accounting/budgets/${id}/activate`),
    close: (id) => api.post(`/accounting/budgets/${id}/close`),
    getOverrunAlerts: (threshold) => api.get('/accounting/budgets/alerts/overruns', { params: { threshold } }),
    getStats: () => api.get('/accounting/budgets/stats/summary')
}

// Currencies API
export const currenciesAPI = {
    list: () => api.get('/accounting/currencies/'),
    create: (data) => api.post('/accounting/currencies/', data),
    update: (id, data) => api.put(`/accounting/currencies/${id}`, data),
    delete: (id) => api.delete(`/accounting/currencies/${id}`),
    addRate: (data) => api.post('/accounting/currencies/rates', data),
    getHistory: (id, limit = 30) => api.get(`/accounting/currencies/${id}/rates`, { params: { limit } }),
    revaluate: (data) => api.post('/accounting/currencies/revaluate', data)
}

// Sales API
export const salesAPI = {
    listCustomers: (params) => api.get('/sales/customers', { params }),
    createCustomer: (data) => api.post('/sales/customers', data),
    listInvoices: (params) => api.get('/sales/invoices', { params }),
    createInvoice: (data) => api.post('/sales/invoices', data),
    getInvoice: (id) => api.get(`/sales/invoices/${id}`),
    cancelInvoice: (id) => api.post(`/sales/invoices/${id}/cancel`),

    // Sales Orders
    listOrders: (params) => api.get('/sales/orders', { params }),
    getOrder: (id) => api.get(`/sales/orders/${id}`),
    createOrder: (data) => api.post('/sales/orders', data),

    // Quotations
    listQuotations: (params) => api.get('/sales/quotations', { params }),
    getQuotation: (id) => api.get(`/sales/quotations/${id}`),
    createQuotation: (data) => api.post('/sales/quotations', data),

    // Customer Groups
    listCustomerGroups: (params) => api.get('/sales/customer-groups', { params }),
    createCustomerGroup: (data) => api.post('/sales/customer-groups', data),
    updateCustomerGroup: (id, data) => api.put(`/sales/customer-groups/${id}`, data),
    deleteCustomerGroup: (id) => api.delete(`/sales/customer-groups/${id}`),

    // Sales Returns
    listReturns: (params) => api.get('/sales/returns', { params }),
    getReturn: (id) => api.get(`/sales/returns/${id}`),
    createReturn: (data) => api.post('/sales/returns', data),
    approveReturn: (id) => api.post(`/sales/returns/${id}/approve`),

    // Customer Receipts
    createReceipt: (data) => api.post('/sales/receipts', data),
    listReceipts: (params) => api.get('/sales/receipts', { params }),
    getReceipt: (id) => api.get(`/sales/receipts/${id}`),
    getOutstandingInvoices: (customerId, params) => api.get(`/sales/customers/${customerId}/outstanding-invoices`, { params }),
    getInvoicePaymentHistory: (invoiceId) => api.get(`/sales/invoices/${invoiceId}/payment-history`),
    getCustomerTransactions: (customerId, branchId) => api.get(`/sales/customers/${customerId}/transactions`, { params: { branch_id: branchId } }),

    // Customer Payments (Refunds)
    createPayment: (data) => api.post('/sales/payments', data),
    listPayments: (params) => api.get('/sales/payments', { params }),
    getPayment: (id) => api.get(`/sales/payments/${id}`),

    // Sales Credit Notes
    listCreditNotes: (params) => api.get('/sales/credit-notes', { params }),
    getCreditNote: (id) => api.get(`/sales/credit-notes/${id}`),
    createCreditNote: (data) => api.post('/sales/credit-notes', data),

    // Sales Debit Notes
    listDebitNotes: (params) => api.get('/sales/debit-notes', { params }),
    getDebitNote: (id) => api.get(`/sales/debit-notes/${id}`),
    createDebitNote: (data) => api.post('/sales/debit-notes', data),

    getSummary: (params) => api.get('/sales/summary', { params }),

    // Phase 8.12 - Sales Improvements
    convertQuotation: (sqId) => api.post(`/sales/quotations/${sqId}/convert`),
    // Commissions
    listCommissionRules: () => api.get('/sales/commissions/rules'),
    createCommissionRule: (data) => api.post('/sales/commissions/rules', data),
    listCommissions: (params) => api.get('/sales/commissions', { params }),
    calculateCommissions: (data) => api.post('/sales/commissions/calculate', data),
    getCommissionSummary: (params) => api.get('/sales/commissions/summary', { params }),
    // Partial Invoicing
    createPartialInvoice: (orderId, data) => api.post(`/sales/orders/${orderId}/partial-invoice`, data),
    // Credit Limit
    getCreditStatus: (partyId) => api.get(`/sales/customers/${partyId}/credit-status`),
    updateCreditLimit: (partyId, data) => api.put(`/sales/customers/${partyId}/credit-limit`, data),
    checkCredit: (data) => api.post('/sales/credit-check', data),
}

// Purchases API
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

// Inventory API
export const inventoryAPI = {
    listProducts: (params) => api.get('/inventory/products', { params }),
    getProduct: (id) => api.get(`/inventory/products/${id}`),
    getProductStock: (id, warehouseId) => api.get(`/inventory/products/${id}/stock`, { params: { warehouse_id: warehouseId } }),
    createProduct: (data) => api.post('/inventory/products', data),
    updateProduct: (id, data) => api.put(`/inventory/products/${id}`, data),
    deleteProduct: (id) => api.delete(`/inventory/products/${id}`),
    listSuppliers: (params) => api.get('/inventory/suppliers', { params }),
    getSupplier: (id) => api.get(`/inventory/suppliers/${id}`),
    createSupplier: (data) => api.post('/inventory/suppliers', data),
    updateSupplier: (id, data) => api.put(`/inventory/suppliers/${id}`, data),
    deleteSupplier: (id) => api.delete(`/inventory/suppliers/${id}`),
    // Categories
    listCategories: (params) => api.get('/inventory/categories', { params }),
    createCategory: (data) => api.post('/inventory/categories', data),
    updateCategory: (id, data) => api.put(`/inventory/categories/${id}`, data),
    deleteCategory: (id) => api.delete(`/inventory/categories/${id}`),
    getNextCategoryCode: () => api.get('/inventory/categories/next-code'),

    // Warehouses
    listWarehouses: (params) => api.get('/inventory/warehouses', { params }),
    createWarehouse: (data) => api.post('/inventory/warehouses', data),
    updateWarehouse: (id, data) => api.put(`/inventory/warehouses/${id}`, data),
    deleteWarehouse: (id) => api.delete(`/inventory/warehouses/${id}`),
    getWarehouse: (id) => api.get(`/inventory/warehouses/${id}`),
    // Renamed to force update and avoid cache
    getWarehouseSpecificStock: (id) => api.get(`/inventory/warehouses/${id}/current-stock?t=${new Date().getTime()}`),

    // Transfers
    transferStock: (data) => api.post('/inventory/transfer', data),
    createStockReceipt: (data) => api.post('/inventory/receipt', data),
    createStockDelivery: (data) => api.post('/inventory/delivery', data),


    getSummary: (params) => api.get('/inventory/summary', { params }),

    // Price Lists
    listPriceLists: () => api.get('/inventory/price-lists'),
    createPriceList: (data) => api.post('/inventory/price-lists', data),
    updatePriceList: (id, data) => api.put(`/inventory/price-lists/${id}`, data),
    deletePriceList: (id) => api.delete(`/inventory/price-lists/${id}`),
    getPriceListItems: (id) => api.get(`/inventory/price-lists/${id}/items`),
    updatePriceListItems: (id, items) => api.post(`/inventory/price-lists/${id}/items`, items),
    getInventoryBalance: (params) => api.get('/inventory/warehouse-stock', { params }),

    // Stock Movements
    getStockMovements: (params) => api.get('/inventory/movements', { params }),

    // Shipments
    createShipment: (data) => api.post('/inventory/shipments', data),
    listShipments: (params) => api.get('/inventory/shipments', { params }),
    getIncomingShipments: (params) => api.get('/inventory/shipments/incoming', { params }),
    getShipmentDetails: (id) => api.get(`/inventory/shipments/${id}`),
    confirmShipment: (id) => api.post(`/inventory/shipments/${id}/confirm`),
    cancelShipment: (id) => api.post(`/inventory/shipments/${id}/cancel`),

    // Notifications
    getNotifications: () => api.get('/inventory/notifications'),
    getUnreadCount: () => api.get('/inventory/notifications/unread-count'),
    markNotificationRead: (id) => api.post(`/inventory/notifications/${id}/read`),
    markAllNotificationsRead: () => api.post('/inventory/notifications/read-all'),

    // Stock Adjustments
    listAdjustments: (params) => api.get('/inventory/adjustments', { params }),
    createAdjustment: (data) => api.post('/inventory/adjustments', data),
    getValuationReport: (params) => api.get('/inventory/valuation-report', { params }),

    // Batches (INV-101)
    listBatches: (params) => api.get('/inventory/batches', { params }),
    getBatch: (id) => api.get(`/inventory/batches/${id}`),
    createBatch: (data) => api.post('/inventory/batches', data),
    updateBatch: (id, data) => api.put(`/inventory/batches/${id}`, data),
    getProductBatches: (productId, params) => api.get(`/inventory/batches/product/${productId}`, { params }),
    getExpiryAlerts: (params) => api.get('/inventory/batches/expiry-alerts', { params }),

    // Serial Numbers (INV-102)
    listSerials: (params) => api.get('/inventory/serials', { params }),
    getSerial: (id) => api.get(`/inventory/serials/${id}`),
    createSerial: (data) => api.post('/inventory/serials', data),
    createSerialsBulk: (data) => api.post('/inventory/serials/bulk', data),
    updateSerial: (id, data) => api.put(`/inventory/serials/${id}`, data),
    lookupSerial: (serialNumber) => api.get(`/inventory/serials/lookup/${serialNumber}`),

    // Product Tracking Config
    updateProductTracking: (productId, params) => api.put(`/inventory/products/${productId}/tracking`, null, { params }),

    // Quality Control (INV-104)
    listQualityInspections: (params) => api.get('/inventory/quality-inspections', { params }),
    getQualityInspection: (id) => api.get(`/inventory/quality-inspections/${id}`),
    createQualityInspection: (data) => api.post('/inventory/quality-inspections', data),
    completeQualityInspection: (id, data) => api.put(`/inventory/quality-inspections/${id}/complete`, data),

    // Cycle Counts (INV-105)
    listCycleCounts: (params) => api.get('/inventory/cycle-counts', { params }),
    getCycleCount: (id) => api.get(`/inventory/cycle-counts/${id}`),
    createCycleCount: (data) => api.post('/inventory/cycle-counts', data),
    startCycleCount: (id) => api.put(`/inventory/cycle-counts/${id}/start`),
    completeCycleCount: (id, data) => api.put(`/inventory/cycle-counts/${id}/complete`, data)
}

// HR API
export const hrAPI = {
    listEmployees: (params) => api.get('/hr/employees', { params }),
    createEmployee: (data) => api.post('/hr/employees', data),
    getEmployee: (id) => api.get(`/hr/employees/${id}`),
    updateEmployee: (id, data) => api.put(`/hr/employees/${id}`, data),

    // Payroll
    listPayrollPeriods: () => api.get('/hr/payroll-periods'),
    createPayrollPeriod: (data) => api.post('/hr/payroll-periods', data),
    getPayrollPeriod: (id) => api.get(`/hr/payroll-periods/${id}`),
    getPayrollEntries: (id, params) => api.get(`/hr/payroll-periods/${id}/entries`, { params }),
    generatePayroll: (id) => api.post(`/hr/payroll-periods/${id}/generate`),
    postPayroll: (id) => api.post(`/hr/payroll-periods/${id}/post`),

    // Configuration
    listDepartments: () => api.get('/hr/departments'),
    createDepartment: (data) => api.post('/hr/departments', data),
    deleteDepartment: (id) => api.delete(`/hr/departments/${id}`),

    listPositions: () => api.get('/hr/positions'),
    createPosition: (data) => api.post('/hr/positions', data),
    deletePosition: (id) => api.delete(`/hr/positions/${id}`),

    // Loans
    listLoans: (params) => api.get('/hr/loans', { params }),
    createLoan: (data) => api.post('/hr/loans', data),
    approveLoan: (id) => api.put(`/hr/loans/${id}/approve`),

    // Leave Requests
    listLeaveRequests: (params) => api.get('/hr/leaves', { params }),
    createLeaveRequest: (data) => api.post('/hr/leaves', data),
    updateLeaveStatus: (id, status) => api.put(`/hr/leaves/${id}/status`, null, { params: { status_in: status } })
}

// HR Advanced API (Phase 4)
export const hrAdvancedAPI = {
    // Salary Structures
    listSalaryStructures: () => api.get('/hr-advanced/salary-structures'),
    createSalaryStructure: (data) => api.post('/hr-advanced/salary-structures', data),
    updateSalaryStructure: (id, data) => api.put(`/hr-advanced/salary-structures/${id}`, data),
    deleteSalaryStructure: (id) => api.delete(`/hr-advanced/salary-structures/${id}`),

    // Salary Components
    listSalaryComponents: (params) => api.get('/hr-advanced/salary-components', { params }),
    createSalaryComponent: (data) => api.post('/hr-advanced/salary-components', data),
    updateSalaryComponent: (id, data) => api.put(`/hr-advanced/salary-components/${id}`, data),

    // Employee Salary Components
    getEmployeeSalaryComponents: (empId) => api.get(`/hr-advanced/employee-salary-components/${empId}`),
    assignSalaryComponent: (data) => api.post('/hr-advanced/employee-salary-components', data),

    // Overtime
    listOvertime: (params) => api.get('/hr-advanced/overtime', { params }),
    createOvertime: (data) => api.post('/hr-advanced/overtime', data),
    approveOvertime: (id, data) => api.put(`/hr-advanced/overtime/${id}/approve`, data),

    // GOSI
    getGOSISettings: () => api.get('/hr-advanced/gosi-settings'),
    saveGOSISettings: (data) => api.post('/hr-advanced/gosi-settings', data),
    calculateGOSI: () => api.get('/hr-advanced/gosi-calculation'),

    // Documents
    listDocuments: (params) => api.get('/hr-advanced/documents', { params }),
    createDocument: (data) => api.post('/hr-advanced/documents', data),
    updateDocument: (id, data) => api.put(`/hr-advanced/documents/${id}`, data),
    deleteDocument: (id) => api.delete(`/hr-advanced/documents/${id}`),

    // Performance Reviews
    listPerformanceReviews: (params) => api.get('/hr-advanced/performance-reviews', { params }),
    createPerformanceReview: (data) => api.post('/hr-advanced/performance-reviews', data),
    updatePerformanceReview: (id, data) => api.put(`/hr-advanced/performance-reviews/${id}`, data),

    // Training
    listTraining: () => api.get('/hr-advanced/training'),
    createTraining: (data) => api.post('/hr-advanced/training', data),
    updateTraining: (id, data) => api.put(`/hr-advanced/training/${id}`, data),
    listParticipants: (id) => api.get(`/hr-advanced/training/${id}/participants`),
    addParticipant: (id, data) => api.post(`/hr-advanced/training/${id}/participants`, data),
    updateParticipant: (id, data) => api.put(`/hr-advanced/training/participants/${id}`, data),

    // Violations
    listViolations: (params) => api.get('/hr-advanced/violations', { params }),
    createViolation: (data) => api.post('/hr-advanced/violations', data),
    updateViolation: (id, data) => api.put(`/hr-advanced/violations/${id}`, data),

    // Custody
    listCustody: (params) => api.get('/hr-advanced/custody', { params }),
    createCustody: (data) => api.post('/hr-advanced/custody', data),
    updateCustody: (id, data) => api.put(`/hr-advanced/custody/${id}`, data),
    returnCustody: (id, data) => api.put(`/hr-advanced/custody/${id}/return`, data),
}

// Assets API
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
}

// Treasury API
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
}

// Reconciliation API
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

// Roles API
export const rolesAPI = {
    list: () => api.get('/roles/'),
    get: (id) => api.get(`/roles/${id}`),
    create: (data) => api.post('/roles/', data),
    update: (id, data) => api.put(`/roles/${id}`, data),
    delete: (id) => api.delete(`/roles/${id}`),
    listPermissions: () => api.get('/roles/permissions')
}

export const branchesAPI = {
    list: () => api.get('/branches'),
    create: (data) => api.post('/branches', data),
    update: (id, data) => api.put(`/branches/${id}`, data),
    delete: (id) => api.delete(`/branches/${id}`)
}

export const attendanceAPI = {
    checkIn: () => api.post('/hr/attendance/check-in'),
    checkOut: () => api.post('/hr/attendance/check-out'),
    getStatus: () => api.get('/hr/attendance/status'),
    getHistory: (params) => api.get('/hr/attendance/history', { params })
}

export const settingsAPI = {
    get: () => api.get('/settings/'),
    updateBulk: (settings) => api.post('/settings/bulk', { settings })
}

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

    listOrders: () => api.get('/manufacturing/orders'),
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
    createMaintenanceLog: (data) => api.post('/manufacturing/maintenance-logs', data)
}

export const contractsAPI = {
    listContracts: (params) => api.get('/contracts', { params }),
    getContract: (id) => api.get(`/contracts/${id}`),
    createContract: (data) => api.post('/contracts', data),
    updateContract: (id, data) => api.put(`/contracts/${id}`, data),
    renewContract: (id) => api.post(`/contracts/${id}/renew`),
    cancelContract: (id) => api.post(`/contracts/${id}/cancel`),
    generateInvoice: (id) => api.post(`/contracts/${id}/generate-invoice`),
    getExpiringContracts: (days = 30) => api.get('/contracts/alerts/expiring', { params: { days } }),
    getContractStats: () => api.get('/contracts/stats/summary')
}


export const costingPolicyAPI = {
    getCurrent: () => api.get('/costing-policies/current'),
    getHistory: () => api.get('/costing-policies/history'),
    setPolicy: (data) => api.post('/costing-policies/set', data)
}

export const taxesAPI = {
    getVATReport: (params) => api.get('/taxes/vat-report', { params }),
    getTaxAudit: (params) => api.get('/taxes/audit-report', { params }),
    getSummary: () => api.get('/taxes/summary'),
    // Tax Rates
    listRates: (params) => api.get('/taxes/rates', { params }),
    getRate: (id) => api.get(`/taxes/rates/${id}`),
    createRate: (data) => api.post('/taxes/rates', data),
    updateRate: (id, data) => api.put(`/taxes/rates/${id}`, data),
    deleteRate: (id) => api.delete(`/taxes/rates/${id}`),
    // Tax Groups
    listGroups: () => api.get('/taxes/groups'),
    createGroup: (data) => api.post('/taxes/groups', data),
    // Tax Returns
    listReturns: (params) => api.get('/taxes/returns', { params }),
    getReturn: (id) => api.get(`/taxes/returns/${id}`),
    createReturn: (data) => api.post('/taxes/returns', data),
    fileReturn: (id, data) => api.put(`/taxes/returns/${id}/file`, data),
    cancelReturn: (id) => api.put(`/taxes/returns/${id}/cancel`),
    // Tax Payments
    listPayments: (params) => api.get('/taxes/payments', { params }),
    createPayment: (data) => api.post('/taxes/payments', data),
    // Settlement
    settle: (data) => api.post('/taxes/settle', data)
}

export const projectsAPI = {
    list: (params) => api.get('/projects/', { params }),
    summary: () => api.get('/projects/summary'),
    get: (id) => api.get(`/projects/${id}`),
    create: (data) => api.post('/projects/', data),
    update: (id, data) => api.put(`/projects/${id}`, data),
    delete: (id) => api.delete(`/projects/${id}`),
    getTasks: (id) => api.get(`/projects/${id}/tasks`),
    createTask: (id, data) => api.post(`/projects/${id}/tasks`, data),
    updateTask: (id, tid, data) => api.put(`/projects/${id}/tasks/${tid}`, data),
    deleteTask: (id, tid) => api.delete(`/projects/${id}/tasks/${tid}`),
    getExpenses: (id) => api.get(`/projects/${id}/expenses`),
    createExpense: (id, data) => api.post(`/projects/${id}/expenses`, data),
    getRevenues: (id) => api.get(`/projects/${id}/revenues`),
    createRevenue: (id, data) => api.post(`/projects/${id}/revenues`, data),
    getFinancials: (id) => api.get(`/projects/${id}/financials`),
    listTimesheets: (id) => api.get(`/projects/${id}/timesheets`),
    createTimesheet: (id, data) => api.post(`/projects/${id}/timesheets`, data),
    updateTimesheet: (id, data) => api.put(`/projects/timesheets/${id}`, data),
    deleteTimesheet: (id) => api.delete(`/projects/timesheets/${id}`),
    approveTimesheets: (id, data) => api.post(`/projects/${id}/timesheets/approve`, data),
    getResourceAllocation: (params) => api.get('/projects/resources/allocation', { params }),

    // Documents
    uploadDocument: (id, formData) => api.post(`/projects/${id}/documents`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }),
    getDocuments: (id) => api.get(`/projects/${id}/documents`),
    deleteDocument: (id, docId) => api.delete(`/projects/${id}/documents/${docId}`),

    // Invoicing
    createInvoice: (id, data) => api.post(`/projects/${id}/create-invoice`, data),
}

export const notificationsAPI = {
    getAll: () => api.get('/notifications'),
    getUnreadCount: () => api.get('/notifications/unread-count'),
    markRead: (id) => api.put(`/notifications/${id}/read`),
    markAllRead: () => api.post('/notifications/read-all'),
}

export const customReportsAPI = {
    create: (data) => api.post('/reports/custom', data),
    list: () => api.get('/reports/custom'),
    get: (id) => api.get(`/reports/custom/${id}`),
    delete: (id) => api.delete(`/reports/custom/${id}`),
    preview: (data) => api.post('/reports/custom/preview', data),
}

const cleanParams = (params) => {
    if (!params) return params;
    const cleaned = {};
    for (const [key, value] of Object.entries(params)) {
        if (value !== '' && value !== null && value !== undefined) {
            cleaned[key] = value;
        }
    }
    return cleaned;
};

export const expensesAPI = {
    list: (params) => api.get('/expenses/', { params: cleanParams(params) }),
    summary: (params) => api.get('/expenses/summary', { params: cleanParams(params) }),
    get: (id) => api.get(`/expenses/${id}`),
    create: (data) => api.post('/expenses/', data),
    update: (id, data) => api.put(`/expenses/${id}`, data),
    approve: (id, data) => api.post(`/expenses/${id}/approve`, data),
    delete: (id) => api.delete(`/expenses/${id}`),
    getReportByType: (params) => api.get('/expenses/reports/by-type', { params: cleanParams(params) }),
    getReportByCostCenter: (params) => api.get('/expenses/reports/by-cost-center', { params: cleanParams(params) }),
    getReportMonthly: (params) => api.get('/expenses/reports/monthly', { params: cleanParams(params) }),
}


export const checksAPI = {
    // Checks Receivable
    listReceivable: (params) => api.get('/checks/receivable', { params }),
    getReceivable: (id) => api.get(`/checks/receivable/${id}`),
    createReceivable: (data) => api.post('/checks/receivable', data),
    collectReceivable: (id, data) => api.post(`/checks/receivable/${id}/collect`, data),
    bounceReceivable: (id, data) => api.post(`/checks/receivable/${id}/bounce`, data),
    receivableStats: (params) => api.get('/checks/receivable/summary/stats', { params }),
    // Checks Payable
    listPayable: (params) => api.get('/checks/payable', { params }),
    getPayable: (id) => api.get(`/checks/payable/${id}`),
    createPayable: (data) => api.post('/checks/payable', data),
    clearPayable: (id, data) => api.post(`/checks/payable/${id}/clear`, data),
    bouncePayable: (id, data) => api.post(`/checks/payable/${id}/bounce`, data),
    payableStats: (params) => api.get('/checks/payable/summary/stats', { params }),
    // Alerts
    getDueAlerts: (params) => api.get('/checks/due-alerts', { params }),
}

export const notesAPI = {
    // Notes Receivable
    listReceivable: (params) => api.get('/notes/receivable', { params }),
    getReceivable: (id) => api.get(`/notes/receivable/${id}`),
    createReceivable: (data) => api.post('/notes/receivable', data),
    collectReceivable: (id, data) => api.post(`/notes/receivable/${id}/collect`, data),
    protestReceivable: (id, data) => api.post(`/notes/receivable/${id}/protest`, data),
    receivableStats: (params) => api.get('/notes/receivable/summary/stats', { params }),
    // Notes Payable
    listPayable: (params) => api.get('/notes/payable', { params }),
    getPayable: (id) => api.get(`/notes/payable/${id}`),
    createPayable: (data) => api.post('/notes/payable', data),
    payPayable: (id, data) => api.post(`/notes/payable/${id}/pay`, data),
    protestPayable: (id, data) => api.post(`/notes/payable/${id}/protest`, data),
    payableStats: (params) => api.get('/notes/payable/summary/stats', { params }),
    // Alerts
    getDueAlerts: (params) => api.get('/notes/due-alerts', { params }),
}

export const scheduledReportsAPI = {
    list: (params) => api.get('/reports/scheduled', { params }),
    create: (data) => api.post('/reports/scheduled', data),
    update: (id, data) => api.put(`/reports/scheduled/${id}`, data),
    delete: (id) => api.delete(`/reports/scheduled/${id}`),
    toggle: (id, active) => api.put(`/reports/scheduled/${id}/toggle`, null, { params: { active } })
}

// Phase 8.10 - POS Improvements API
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

// Phase 8.13 - Budget Improvements API
export const budgetImprovementsAPI = {
    createByCostCenter: (data) => api.post('/budgets/by-cost-center', data),
    getByCostCenter: (ccId) => api.get(`/budgets/by-cost-center/${ccId}`),
    getMultiYear: (params) => api.get('/budgets/multi-year', { params }),
    getComparison: (params) => api.get('/budgets/comparison', { params }),
}

// Phase 8.15 - HR Improvements API
export const hrImprovementsAPI = {
    // Payslips
    listPayslips: (params) => api.get('/hr/payslips', { params }),
    generatePayslip: (data) => api.post('/hr/payslips/generate', data),
    getPayslip: (entryId) => api.get(`/hr/payslips/${entryId}`),
    getEmployeePayslips: (empId, params) => api.get(`/hr/employees/${empId}/payslips`, { params }),
    // Leave Balance & Carryover
    getLeaveBalance: (empId) => api.get(`/hr/leave-balance/${empId}`),
    calculateLeaveCarryover: (data) => api.post('/hr/leave-carryover/calculate', data),
    // Recruitment
    listJobOpenings: (params) => api.get('/hr/recruitment/openings', { params }),
    createJobOpening: (data) => api.post('/hr/recruitment/openings', data),
    updateJobOpening: (id, data) => api.put(`/hr/recruitment/openings/${id}`, data),
    listApplications: (openingId) => api.get(`/hr/recruitment/openings/${openingId}/applications`),
    listAllApplications: () => api.get('/hr/recruitment/applications'),
    createApplication: (data) => api.post('/hr/recruitment/applications', data),
    updateApplicationStage: (id, data) => api.put(`/hr/recruitment/applications/${id}/stage`, data),
}
// Attach specific APIs to default export for ease of use in some components
api.costingPolicy = costingPolicyAPI
api.branches = branchesAPI

// Phase 9 - CRM API
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

// Phase 9 - External Integrations API
export const externalAPI = {
    // API Keys
    listApiKeys: () => api.get('/external/api-keys'),
    createApiKey: (data) => api.post('/external/api-keys', data),
    deleteApiKey: (id) => api.delete(`/external/api-keys/${id}`),
    // Webhooks
    getWebhookEvents: () => api.get('/external/webhooks/events'),
    listWebhooks: () => api.get('/external/webhooks'),
    createWebhook: (data) => api.post('/external/webhooks', data),
    updateWebhook: (id, data) => api.put(`/external/webhooks/${id}`, data),
    deleteWebhook: (id) => api.delete(`/external/webhooks/${id}`),
    getWebhookLogs: (id) => api.get(`/external/webhooks/${id}/logs`),
    // ZATCA
    generateQR: (invoiceId) => api.post('/external/zatca/generate-qr', { invoice_id: invoiceId }),
    generateZatcaKeypair: () => api.post('/external/zatca/generate-keypair'),
    verifyZatca: (invoiceId) => api.get(`/external/zatca/verify/${invoiceId}`),
    // WHT
    listWhtRates: () => api.get('/external/wht/rates'),
    createWhtRate: (data) => api.post('/external/wht/rates', data),
    calculateWht: (data) => api.post('/external/wht/calculate', data),
    listWhtTransactions: (params) => api.get('/external/wht/transactions', { params }),
    createWhtTransaction: (data) => api.post('/external/wht/transactions', data),
}

// Export both as default and named export for flexibility
export { api }
export default api

