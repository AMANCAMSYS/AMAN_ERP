/**
 * API barrel — backward-compatible re-export layer.
 *
 * All API services have been moved to /src/services/ (one file per domain).
 * This file re-exports everything so existing imports like:
 *   import { salesAPI } from '../utils/api'
 *   import api from '../../utils/api'
 * continue to work with zero changes across 205+ consumer files.
 *
 * For new code, prefer importing directly from services:
 *   import { salesAPI } from '@/services/sales'
 */

// Core axios instance (default + named export)
export { default, api } from '../services/apiClient'

// Auth & Companies
export { authAPI } from '../services/auth'
export { companiesAPI } from '../services/companies'

// Accounting & Finance
export { accountingAPI, costCentersAPI, budgetsAPI, budgetImprovementsAPI, currenciesAPI } from '../services/accounting'

// Reports
export { reportsAPI, customReportsAPI, scheduledReportsAPI, detailedReportsAPI, reportSharingAPI } from '../services/reports'

// Sales & Purchases
export { salesAPI } from '../services/sales'
export { purchasesAPI } from '../services/purchases'

// Inventory & Costing
export { inventoryAPI, costingPolicyAPI } from '../services/inventory'

// HR
export { hrAPI, hrAdvancedAPI, hrImprovementsAPI, attendanceAPI } from '../services/hr'

// Assets
export { assetsAPI } from '../services/assets'

// Treasury & Reconciliation
export { treasuryAPI, reconciliationAPI } from '../services/treasury'

// Manufacturing
export { manufacturingAPI } from '../services/manufacturing'

// Contracts
export { contractsAPI } from '../services/contracts'

// Taxes
export { taxesAPI, taxComplianceAPI } from '../services/taxes'

// Projects
export { projectsAPI } from '../services/projects'

// Notifications
export { notificationsAPI } from '../services/notifications'

// Expenses
export { expensesAPI } from '../services/expenses'

// Checks & Notes
export { checksAPI, notesAPI } from '../services/checks'

// POS
export { posAPI } from '../services/pos'

// Settings, Roles & Branches
export { settingsAPI, rolesAPI, branchesAPI } from '../services/settings'

// CRM
export { crmAPI } from '../services/crm'

// External Integrations
export { externalAPI } from '../services/external'

