/**
 * Service layer barrel export.
 * All API services are grouped by domain in separate files.
 *
 * Usage (direct):
 *   import { salesAPI } from '@/services'
 *
 * Usage (via legacy path, backward-compatible):
 *   import { salesAPI } from '../utils/api'
 */

// Core axios instance
export { default as api, default, cleanParams } from './apiClient'

// Auth & Companies
export { authAPI } from './auth'
export { companiesAPI } from './companies'

// Accounting & Finance
export { accountingAPI, costCentersAPI, budgetsAPI, budgetImprovementsAPI, currenciesAPI } from './accounting'

// Reports
export { reportsAPI, customReportsAPI, scheduledReportsAPI } from './reports'

// Sales & Purchases
export { salesAPI } from './sales'
export { purchasesAPI } from './purchases'

// Inventory & Costing
export { inventoryAPI, costingPolicyAPI } from './inventory'

// HR
export { hrAPI, hrAdvancedAPI, hrImprovementsAPI, attendanceAPI } from './hr'

// Assets
export { assetsAPI } from './assets'

// Treasury & Reconciliation
export { treasuryAPI, reconciliationAPI } from './treasury'

// Manufacturing
export { manufacturingAPI } from './manufacturing'

// Contracts
export { contractsAPI } from './contracts'

// Taxes
export { taxesAPI } from './taxes'

// Projects
export { projectsAPI } from './projects'

// Notifications
export { notificationsAPI } from './notifications'

// Expenses
export { expensesAPI } from './expenses'

// Checks & Notes
export { checksAPI, notesAPI } from './checks'

// POS
export { posAPI } from './pos'

// Settings, Roles & Branches
export { settingsAPI, rolesAPI, branchesAPI } from './settings'

// CRM
export { crmAPI } from './crm'

// External Integrations
export { externalAPI } from './external'
