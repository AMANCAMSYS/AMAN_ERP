import { NavLink } from 'react-router-dom'
import { logout, getUser, hasPermission } from '../utils/auth'
import { useTranslation } from 'react-i18next'

function Sidebar() {
    const { t } = useTranslation()
    const user = getUser()
    const navItems = [
        { path: '/dashboard', label: t('nav.workspace'), icon: '🏠' },
    ]

    if (user?.role === 'system_admin') {
        navItems.push({ path: '/admin/companies', label: t('nav.companies'), icon: '🏢' })
    } else {
        if (hasPermission('accounting.view')) {
            navItems.push({ path: '/accounting', label: t('nav.accounting'), icon: '📊' })
        }
        if (hasPermission('assets.view')) {
            navItems.push({ path: '/assets', label: t('nav.assets') || 'الأصول الثابتة', icon: '🏢' })
        }
        if (hasPermission('treasury.view')) {
            navItems.push({ path: '/treasury', label: t('nav.treasury'), icon: '🏦' })
        }
        if (hasPermission('reconciliation.view')) {
            navItems.push({ path: '/treasury/reconciliation', label: t('nav.reconciliation') || 'تسوية البنك', icon: '⚖️' })
        }
        if (hasPermission('sales.view')) {
            navItems.push({ path: '/sales', label: t('nav.sales'), icon: '💰' })
        }
        // POS Module
        if (hasPermission(['sales.view', 'pos.view'])) {
            navItems.push({ path: '/pos', label: t('nav.pos') || 'نقاط البيع', icon: '🏪' })
        }

        if (hasPermission('buying.view')) {
            navItems.push({ path: '/buying', label: t('nav.buying'), icon: '🛒' })
        }
        if (hasPermission(['stock.view', 'stock.reports'])) {
            navItems.push({ path: '/stock', label: t('nav.inventory'), icon: '📦' })
        }
        // Manufacturing Module
        if (hasPermission(['manufacturing.view', 'stock.view'])) {
            navItems.push({ path: '/manufacturing', label: t('nav.manufacturing') || 'التصنيع', icon: '🏭' })
        }
        // Projects Module
        if (hasPermission('projects.view')) {
            navItems.push({ path: '/projects', label: t('nav.projects') || 'المشاريع', icon: '📐' })
        }
        // CRM Module
        if (hasPermission('sales.view')) {
            navItems.push({ path: '/crm', label: 'إدارة العلاقات', icon: '🤝' })
        }
        // Expenses Module
        if (hasPermission('expenses.view')) {
            navItems.push({ path: '/expenses', label: t('nav.expenses') || 'المصاريف', icon: '💰' })
        }
        // Taxes Module
        if (hasPermission('accounting.view')) {
            navItems.push({ path: '/taxes', label: t('nav.taxes') || 'الضرائب', icon: '🧾' })
        }
        if (hasPermission('approvals.view')) {
            navItems.push({ path: '/approvals', label: t('nav.approvals') || 'الاعتمادات', icon: '✅' })
        }
        if (hasPermission('reports.view') || hasPermission('reports.financial') || hasPermission('sales.reports') || hasPermission('stock.reports')) {
            navItems.push({ path: '/reports', label: t('nav.reports'), icon: '📈' })
        }
        if (hasPermission('hr.view')) {
            navItems.push({ path: '/hr', label: t('nav.hr'), icon: '👥' })
        }
        if (hasPermission('audit.view')) {
            navItems.push({ path: '/admin/audit-logs', label: t('nav.auditLogs') || 'سجلات المراقبة', icon: '📋' })
        }
        if (hasPermission('admin.roles')) {
            navItems.push({ path: '/admin/roles', label: t('nav.roles') || 'إدارة الأدوار', icon: '🔐' })
        }
        if (hasPermission('branches.view')) {
            navItems.push({ path: '/settings/branches', label: t('nav.branches') || 'الفروع', icon: '🏢' })
        }
        if (hasPermission('admin.companies')) {
            navItems.push({ path: '/settings/costing-policy', label: t('nav.costingPolicy') || 'سياسات التكلفة', icon: '💲' })
            navItems.push({ path: '/data-import', label: t('nav.dataImport') || 'استيراد البيانات', icon: '📥' })
            navItems.push({ path: '/settings/api-keys', label: 'مفاتيح API', icon: '🔑' })
            navItems.push({ path: '/settings/webhooks', label: 'الويب هوك', icon: '🔗' })
            navItems.push({ path: '/settings', label: t('nav.settings'), icon: '⚙️' })
        }
    }

    return (
        <aside className="sidebar">
            <div className="sidebar-brand">
                AMAN ERP
            </div>
            <nav className="sidebar-nav">
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        end={item.path === '/treasury' || item.path === '/settings'}
                        className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}
                    >
                        <span className="nav-icon">{item.icon}</span>
                        <span className="nav-label">{item.label}</span>
                    </NavLink>
                ))}
            </nav>
        </aside>
    )
}

export default Sidebar
