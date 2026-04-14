import { NavLink } from 'react-router-dom'
import { logout, getUser, hasPermission } from '../utils/auth'
import { useTranslation } from 'react-i18next'
import { getIndustryType } from '../hooks/useIndustryType'
import { isModuleEnabledForIndustry } from '../config/industryModules'

function Sidebar({ isOpen, isMobile, onClose, onToggle }) {
    const { t } = useTranslation()
    const user = getUser()
    const industryType = getIndustryType()
    const navItems = [
        { path: '/dashboard', label: t('nav.workspace'), icon: '🏠' },
    ]

    if (user?.role === 'system_admin') {
        navItems.push({ path: '/admin/companies', label: t('nav.companies'), icon: '🏢' })
    } else {
        const enabledModules = user?.enabled_modules || []
        const isSystemAdmin = user?.role === 'system_admin'

        // Helper to check if module is enabled
        // أولوية 1: enabled_modules المخزنة في الباك إند (القائمة المخصصة)
        // أولوية 2: مصفوفة النشاط التجاري (الافتراضي)
        // أولوية 3: إذا لم يُحدد شيء → إظهار الكل
        const isModuleEnabled = (moduleKey) => {
            if (isSystemAdmin) return true
            // الأولوية للقائمة المخصصة من enabled_modules
            if (enabledModules && enabledModules.length > 0) {
                return enabledModules.includes(moduleKey)
            }
            // مصفوفة النشاط التجاري (fallback)
            if (industryType) {
                return isModuleEnabledForIndustry(industryType, moduleKey)
            }
            // لم يُعدّ شيء بعد → إظهار الكل
            return true
        }

        if (hasPermission('accounting.view') && isModuleEnabled('accounting')) {
            navItems.push({ path: '/accounting', label: t('nav.accounting'), icon: '📊' })
        }
        // Intercompany (US3)
        if (hasPermission('intercompany.view') && isModuleEnabled('intercompany')) {
            navItems.push({ path: '/accounting/intercompany/entities', label: t('nav.intercompany') || 'محاسبة بين الشركات', icon: '🔄' })
        }
        if (hasPermission('assets.view') && isModuleEnabled('assets')) {
            navItems.push({ path: '/assets', label: t('nav.assets') || 'الأصول الثابتة', icon: '🏗️' })
        }
        if (hasPermission('treasury.view') && isModuleEnabled('treasury')) {
            navItems.push({ path: '/treasury', label: t('nav.treasury'), icon: '🏦' })
        }
        // Keep forecast as a direct sidebar link only if user cannot access Treasury home.
        if (hasPermission('finance.cashflow_view') && !hasPermission('treasury.view')) {
            navItems.push({ path: '/finance/cashflow', label: t('cashflow.title'), icon: '💹' })
        }
        if (hasPermission('finance.subscription_manage')) {
            navItems.push({ path: '/finance/subscriptions', label: t('subscription.title') || 'الاشتراكات', icon: '🔄' })
        }
        if (hasPermission('sales.view') && isModuleEnabled('sales')) {
            navItems.push({ path: '/sales', label: t('nav.sales'), icon: '💰' })
        }
        // CPQ (US13)
        if (hasPermission('sales.cpq_view') && isModuleEnabled('cpq')) {
            navItems.push({ path: '/sales/cpq/products', label: t('nav.cpq') || 'التسعير المتقدم', icon: '🧮' })
        }
        // POS Module
        if (hasPermission(['sales.view', 'pos.view']) && isModuleEnabled('pos')) {
            navItems.push({ path: '/pos', label: t('nav.pos') || 'نقاط البيع', icon: '🏪' })
        }

        if (hasPermission('buying.view') && isModuleEnabled('buying')) {
            navItems.push({ path: '/buying', label: t('nav.buying'), icon: '🛒' })
        }
        // Blanket POs (US10)
        if (hasPermission('buying.blanket_view') && isModuleEnabled('buying')) {
            navItems.push({ path: '/buying/blanket-po', label: t('nav.blanket_po') || 'أوامر شراء شاملة', icon: '📋' })
        }
        // 3-Way Matching (US2)
        if (hasPermission('buying.view') && isModuleEnabled('matching')) {
            navItems.push({ path: '/buying/matching', label: t('nav.matching') || 'المطابقة الثلاثية', icon: '🔗' })
        }
        if (hasPermission(['stock.view', 'stock.reports']) && isModuleEnabled('stock')) {
            navItems.push({ path: '/stock', label: t('nav.inventory'), icon: '📦' })
        }
        // Demand Forecast (US14)
        if (hasPermission('inventory.forecast_view') && isModuleEnabled('forecast')) {
            navItems.push({ path: '/inventory/forecast', label: t('nav.demand_forecast') || 'التنبؤ بالطلب', icon: '📉' })
        }
        // Manufacturing Module
        if (hasPermission(['manufacturing.view', 'stock.view']) && isModuleEnabled('manufacturing')) {
            navItems.push({ path: '/manufacturing', label: t('nav.manufacturing') || 'التصنيع', icon: '🏭' })
        }
        // Shop Floor Control (US15)
        if (hasPermission('manufacturing.shopfloor_view') && isModuleEnabled('shop_floor')) {
            navItems.push({ path: '/manufacturing/shopfloor', label: t('nav.shop_floor') || 'أرضية الإنتاج', icon: '⚙️' })
        }
        // Projects Module
        if (hasPermission('projects.view') && isModuleEnabled('projects')) {
            navItems.push({ path: '/projects', label: t('nav.projects') || 'المشاريع', icon: '📐' })
        }
        // Time Tracking (US17)
        if (hasPermission('projects.time_view') && isModuleEnabled('projects')) {
            navItems.push({ path: '/projects/timetracking', label: t('nav.time_tracking') || 'تتبع الوقت', icon: '⏱️' })
        }
        // Resource Planning (US18)
        if (hasPermission('projects.resource_view') && isModuleEnabled('projects')) {
            navItems.push({ path: '/projects/resources/availability', label: t('nav.resource_planning') || 'تخطيط الموارد', icon: '📅' })
        }
        // CRM Module
        if (hasPermission('sales.view') && isModuleEnabled('crm')) {
            navItems.push({ path: '/crm', label: t('nav.crm'), icon: '🤝' })
        }
        // Campaign Management (US11)
        if (hasPermission('crm.campaign_manage') && isModuleEnabled('crm')) {
            navItems.push({ path: '/crm/campaigns', label: t('nav.campaigns') || 'الحملات', icon: '📣' })
        }
        // Services Module
        if ((hasPermission('services.view') || hasPermission('admin.companies')) && isModuleEnabled('services')) {
            navItems.push({ path: '/services', label: t('nav.services'), icon: '🔧' })
        }
        // Expenses Module
        if (hasPermission('expenses.view') && isModuleEnabled('expenses')) {
            navItems.push({ path: '/expenses', label: t('nav.expenses') || 'المصاريف', icon: '💸' })
        }
        // Taxes Module
        if (hasPermission('accounting.view') && isModuleEnabled('taxes')) {
            navItems.push({ path: '/taxes', label: t('nav.taxes') || 'الضرائب', icon: '🧾' })
        }
        if (hasPermission('approvals.view') && isModuleEnabled('approvals')) {
            navItems.push({ path: '/approvals', label: t('nav.approvals') || 'الاعتمادات', icon: '✅' })
        }
        if (hasPermission('reports.view') || hasPermission('reports.financial') || hasPermission('sales.reports') || hasPermission('stock.reports')) {
            // Reports are usually general but we can tie them to 'reports' module key
            if (isModuleEnabled('reports')) {
                navItems.push({ path: '/reports', label: t('nav.reports'), icon: '📈' })
            }
        }
        if (hasPermission('dashboard.analytics_view')) {
            navItems.push({ path: '/analytics', label: t('analytics.title'), icon: '📊' })
        }
        if (hasPermission('hr.view') && isModuleEnabled('hr')) {
            navItems.push({ path: '/hr', label: t('nav.hr'), icon: '👥' })
        }
        if (hasPermission('hr.self_service') && isModuleEnabled('hr')) {
            navItems.push({ path: '/hr/self-service', label: t('nav.self_service'), icon: '🧑‍💼' })
        }
        // Performance Reviews (US12)
        if (hasPermission('hr.performance_view') && isModuleEnabled('hr')) {
            navItems.push({ path: '/hr/performance/cycles', label: t('nav.performance') || 'تقييم الأداء', icon: '🎯' })
        }
        if (hasPermission('audit.view') && isModuleEnabled('audit')) {
            navItems.push({ path: '/admin/audit-logs', label: t('nav.auditLogs') || 'سجلات المراقبة', icon: '📋' })
        }
        if (hasPermission('data_import.view') && isModuleEnabled('data_import')) {
            navItems.push({ path: '/data-import', label: t('nav.dataImport') || 'استيراد البيانات', icon: '📥' })
        }
        if (hasPermission('admin.roles')) {
            navItems.push({ path: '/admin/roles', label: t('nav.roles') || 'إدارة الأدوار', icon: '🔐' })
        }
        if (hasPermission('branches.view') && !hasPermission('admin.companies')) {
            navItems.push({ path: '/settings/branches', label: t('nav.branches') || 'الفروع', icon: '🏢' })
        }
        if (hasPermission('admin.companies')) {
            navItems.push({ path: '/settings', label: t('nav.settings'), icon: '⚙️' })
        }
    }


    const handleToggleClick = (e) => {
        e.preventDefault()
        e.stopPropagation()
        if (typeof onToggle === 'function') {
            onToggle()
        }
    }

    return (
        <aside className={`sidebar${isOpen ? ' sidebar-open' : ''}`} dir="rtl">
            <div className="sidebar-brand">
                <button
                    className="sidebar-toggle"
                    onClick={handleToggleClick}
                    aria-label={isOpen ? 'إغلاق القائمة' : 'فتح القائمة'}
                    aria-expanded={isOpen}
                    type="button"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <rect width="18" height="18" x="3" y="3" rx="2" />
                        <path d="M3 9h18" />
                    </svg>
                </button>
                <span className="sidebar-brand-text">AMAN ERP</span>
            </div>
            <nav className="sidebar-nav">
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        data-nav-target={item.path}
                        end={item.path === '/treasury' || item.path === '/settings'}
                        className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}
                        onClick={isMobile ? onClose : undefined}
                    >
                        <div className="nav-icon-container">
                            <span className="nav-icon">{item.icon}</span>
                        </div>
                        <span className="nav-label">{item.label}</span>
                    </NavLink>
                ))}
            </nav>
        </aside>
    )
}

export default Sidebar
