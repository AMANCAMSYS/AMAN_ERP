import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ALWAYS_ENABLED_MODULES, VARIABLE_MODULES, INDUSTRY_TYPES, getEnabledModulesForIndustry } from '../../config/industryModules'
import { getIndustryType } from '../../hooks/useIndustryType'
import { getUser, updateUser } from '../../utils/auth'
import api from '../../services/apiClient'

const MODULE_LABELS = {
  dashboard:   { ar: 'مساحة العمل',         en: 'Dashboard',       icon: '🏠', category: 'core' },
  kpi:         { ar: 'لوحات الأداء',         en: 'KPI Dashboards',  icon: '📊', category: 'core' },
  accounting:  { ar: 'المحاسبة',             en: 'Accounting',      icon: '📒', category: 'finance' },
  assets:      { ar: 'الأصول الثابتة',       en: 'Fixed Assets',    icon: '🏗️', category: 'finance' },
  treasury:    { ar: 'الخزينة',              en: 'Treasury',        icon: '🏦', category: 'finance' },
  sales:       { ar: 'المبيعات',             en: 'Sales',           icon: '💰', category: 'sales' },
  buying:      { ar: 'المشتريات',            en: 'Purchases',       icon: '🛒', category: 'sales' },
  crm:         { ar: 'إدارة العلاقات',       en: 'CRM',             icon: '🤝', category: 'sales' },
  expenses:    { ar: 'المصاريف',             en: 'Expenses',        icon: '💸', category: 'finance' },
  taxes:       { ar: 'الضرائب',              en: 'Taxes',           icon: '🧾', category: 'finance' },
  approvals:   { ar: 'الاعتمادات',           en: 'Approvals',       icon: '✅', category: 'core' },
  reports:     { ar: 'التقارير',             en: 'Reports',         icon: '📈', category: 'core' },
  hr:          { ar: 'الموارد البشرية',      en: 'HR & Payroll',    icon: '👥', category: 'hr' },
  audit:       { ar: 'سجلات المراقبة',       en: 'Audit Logs',      icon: '📋', category: 'core' },
  roles:       { ar: 'الأدوار والصلاحيات',   en: 'Roles',           icon: '🔐', category: 'core' },
  settings:    { ar: 'الإعدادات',            en: 'Settings',        icon: '⚙️', category: 'core' },
  data_import: { ar: 'استيراد البيانات',     en: 'Data Import',     icon: '📥', category: 'core' },
  pos:           { ar: 'نقاط البيع',         en: 'Point of Sale',   icon: '🏪', category: 'variable' },
  stock:         { ar: 'المخزون',             en: 'Inventory',       icon: '📦', category: 'variable' },
  manufacturing: { ar: 'التصنيع',             en: 'Manufacturing',   icon: '🏭', category: 'variable' },
  projects:      { ar: 'المشاريع',            en: 'Projects',        icon: '📐', category: 'variable' },
  services:      { ar: 'الخدمات والصيانة',   en: 'Services',        icon: '🔧', category: 'variable' },
}

const CATEGORY_LABELS = {
  core:     { ar: 'وحدات أساسية',     en: 'Core Modules',      color: '#3b82f6' },
  finance:  { ar: 'المالية والمحاسبة', en: 'Finance',           color: '#8b5cf6' },
  sales:    { ar: 'المبيعات والتسويق', en: 'Sales & CRM',       color: '#06b6d4' },
  hr:       { ar: 'الموارد البشرية',   en: 'Human Resources',   color: '#f59e0b' },
  variable: { ar: 'وحدات حسب النشاط', en: 'Industry Modules',  color: '#10b981' },
}

function ModuleCustomization() {
  const { i18n } = useTranslation()
  const navigate = useNavigate()
  const isRTL = i18n.language === 'ar'

  const industryKey = getIndustryType()
  const industry = industryKey ? INDUSTRY_TYPES[industryKey] : null

  const user = getUser()
  const initialEnabled = user?.enabled_modules || (industryKey ? getEnabledModulesForIndustry(industryKey) : [])

  const [variableState, setVariableState] = useState(() => {
    const state = {}
    VARIABLE_MODULES.forEach(m => { state[m] = initialEnabled.includes(m) })
    return state
  })

  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const finalModules = [
    ...ALWAYS_ENABLED_MODULES,
    ...VARIABLE_MODULES.filter(m => variableState[m]),
  ]

  const enabledCount = finalModules.length
  const totalCount = ALWAYS_ENABLED_MODULES.length + VARIABLE_MODULES.length
  const progressPct = Math.round((enabledCount / totalCount) * 100)

  const handleToggle = (moduleKey) => {
    if (ALWAYS_ENABLED_MODULES.includes(moduleKey)) return
    setVariableState(prev => ({ ...prev, [moduleKey]: !prev[moduleKey] }))
  }

  const handleSave = async () => {
    setSaving(true)
    setError('')
    try {
      await api.put('/companies/modules', finalModules)
      updateUser({ enabled_modules: finalModules })
      window.location.href = '/dashboard'
    } catch (err) {
      console.error('Save failed:', err)
      setError(isRTL ? 'فشل الحفظ، حاول مرة أخرى' : 'Save failed, please try again')
      setSaving(false)
    }
  }

  const handleSkip = () => { window.location.href = '/dashboard' }

  const grouped = {}
  Object.entries(MODULE_LABELS).forEach(([key, label]) => {
    const cat = label.category
    if (!grouped[cat]) grouped[cat] = []
    grouped[cat].push({ key, ...label })
  })

  const borderSide = isRTL ? 'right' : 'left'

  return (
    <>
      <style>{`
        .mc-layout {
          min-height: 100vh;
          background: var(--bg-main, #f8fafc);
          padding: 32px 16px 60px;
          direction: ${isRTL ? 'rtl' : 'ltr'};
        }
        .mc-container { width: 100%; max-width: 920px; margin: 0 auto; animation: mcFadeUp 0.3s ease-out; }

        .mc-back-btn {
          display: inline-flex; align-items: center; gap: 6px;
          background: var(--bg-card, #fff); border: 1px solid var(--border-color, #e2e8f0);
          color: var(--text-secondary, #64748b); padding: 8px 16px; border-radius: 8px;
          cursor: pointer; font-size: 14px; font-weight: 600; margin-bottom: 24px; transition: all 0.15s;
        }
        .mc-back-btn:hover { background: var(--bg-hover, #f1f5f9); color: var(--text-main, #1e293b); }

        .mc-industry-badge {
          display: flex; align-items: center; gap: 16px;
          background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 14px;
          padding: 16px 22px; margin-bottom: 24px;
        }
        .mc-industry-label { font-size: 12px; color: #3b82f6; font-weight: 600; margin-bottom: 3px; }
        .mc-industry-name  { font-size: 20px; font-weight: 800; color: var(--text-main, #1e293b); }
        .mc-industry-desc  { font-size: 13px; color: var(--text-secondary, #64748b); margin-top: 2px; }

        .mc-header { margin-bottom: 20px; }
        .mc-header h1 { font-size: 24px; font-weight: 800; color: var(--text-main, #1e293b); margin-bottom: 6px; }
        .mc-header p  { font-size: 14px; color: var(--text-secondary, #64748b); line-height: 1.6; }

        .mc-counter {
          background: var(--bg-card, #fff); border: 1px solid var(--border-color, #e2e8f0);
          border-radius: 14px; padding: 16px 22px; margin-bottom: 24px;
          display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
          box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .mc-counter-badge {
          background: linear-gradient(135deg, #22c55e, #16a34a); color: white;
          font-weight: 800; font-size: 22px; width: 52px; height: 52px;
          border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
        }
        .mc-counter-title { color: var(--text-main, #1e293b); font-weight: 700; font-size: 15px; }
        .mc-counter-sub   { color: var(--text-secondary, #64748b); font-size: 12px; }
        .mc-progress-wrap { flex: 1; min-width: 160px; }
        .mc-progress-bar  { background: var(--border-color, #e2e8f0); border-radius: 999px; height: 8px; overflow: hidden; }
        .mc-progress-fill { height: 100%; background: linear-gradient(90deg, #3b82f6, #22c55e); border-radius: 999px; transition: width 0.3s ease; }

        .mc-group {
          background: var(--bg-card, #fff); border: 1px solid var(--border-color, #e2e8f0);
          border-radius: 14px; overflow: hidden; margin-bottom: 16px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .mc-group-header {
          display: flex; align-items: center; justify-content: space-between; gap: 12px;
          padding: 14px 20px; border-bottom: 1px solid var(--border-color, #e2e8f0);
        }
        .mc-group-title { font-weight: 700; font-size: 15px; color: var(--text-main, #1e293b); }
        .mc-group-desc  { font-size: 12px; color: var(--text-secondary, #64748b); margin-top: 2px; }
        .mc-group-pill  { padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 700; white-space: nowrap; flex-shrink: 0; }

        .mc-modules-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); }
        .mc-module {
          display: flex; align-items: center; gap: 10px; padding: 14px 16px; cursor: pointer;
          border-bottom: 1px solid var(--border-color, #e2e8f0);
          border-${borderSide}: 1px solid var(--border-color, #e2e8f0);
          transition: background 0.15s; background: var(--bg-card, #fff);
        }
        .mc-module:hover { background: var(--bg-hover, #f8fafc); }
        .mc-module.locked { cursor: default; }
        .mc-module.locked:hover { background: var(--bg-card, #fff); }
        .mc-module-icon-wrap {
          width: 36px; height: 36px; border-radius: 9px;
          display: flex; align-items: center; justify-content: center;
          font-size: 18px; flex-shrink: 0; transition: background 0.2s;
        }
        .mc-module-name { font-weight: 600; font-size: 13px; color: var(--text-main, #1e293b); line-height: 1.35; }
        .mc-module-sub  { font-size: 11px; color: var(--text-muted, #94a3b8); margin-top: 1px; }
        .mc-toggle {
          width: 36px; height: 20px; border-radius: 999px; position: relative;
          transition: background 0.2s; flex-shrink: 0;
        }
        .mc-toggle-knob {
          width: 14px; height: 14px; background: white; border-radius: 50%;
          position: absolute; top: 3px; transition: left 0.2s ease;
          box-shadow: 0 1px 3px rgba(0,0,0,0.25);
        }

        .mc-error {
          background: #fef2f2; border: 1px solid #fecaca; color: #dc2626;
          padding: 12px 18px; border-radius: 10px; text-align: center; margin-top: 12px; font-size: 14px;
        }
        .mc-footer { display: flex; gap: 12px; margin-top: 24px; flex-wrap: wrap; }
        .mc-btn-skip {
          flex: 1; min-width: 140px; background: var(--bg-card, #fff);
          border: 1px solid var(--border-color, #e2e8f0); color: var(--text-secondary, #64748b);
          padding: 14px; border-radius: 12px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.15s;
        }
        .mc-btn-skip:hover { background: var(--bg-hover, #f1f5f9); color: var(--text-main, #1e293b); }
        .mc-btn-save {
          flex: 3; min-width: 200px;
          background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white;
          padding: 14px; border-radius: 12px; border: none; font-size: 16px; font-weight: 700;
          cursor: pointer; box-shadow: 0 6px 20px -4px rgba(59,130,246,0.4); transition: opacity 0.15s;
        }
        .mc-btn-save:disabled { opacity: 0.6; cursor: wait; }
        .mc-btn-save:hover:not(:disabled) { opacity: 0.9; }

        @keyframes mcFadeUp {
          from { opacity: 0; transform: translateY(16px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @media (max-width: 600px) {
          .mc-modules-grid { grid-template-columns: 1fr 1fr; }
          .mc-header h1 { font-size: 20px; }
          .mc-industry-badge { flex-direction: column; text-align: center; }
        }
      `}</style>

      <div className="mc-layout">
        <div className="mc-container">

          {/* Back */}
          <button className="mc-back-btn" onClick={() => navigate('/setup/industry')}>
            {isRTL ? '→ تغيير نوع النشاط' : '← Change Business Type'}
          </button>

          {/* Industry badge */}
          {industry && (
            <div className="mc-industry-badge">
              <div style={{ fontSize: '40px', flexShrink: 0 }}>{industry.icon}</div>
              <div>
                <div className="mc-industry-label">{isRTL ? 'نوع النشاط المختار' : 'Selected Business Type'}</div>
                <div className="mc-industry-name">{isRTL ? industry.nameAr : industry.nameEn}</div>
                <div className="mc-industry-desc">{isRTL ? industry.descriptionAr : industry.descriptionEn}</div>
              </div>
            </div>
          )}

          {/* Header */}
          <div className="mc-header">
            <h1>⚙️ {isRTL ? 'تخصيص الوحدات' : 'Customize Modules'}</h1>
            <p>
              {isRTL
                ? 'الوحدات الثابتة مُفعَّلة دائماً ومُقفَلة. يمكنك تفعيل أو تعطيل الوحدات المتغيرة حسب احتياجك.'
                : 'Core modules are always enabled and locked. Toggle variable modules based on your needs.'}
            </p>
          </div>

          {/* Counter */}
          <div className="mc-counter">
            <div className="mc-counter-badge">{enabledCount}</div>
            <div>
              <div className="mc-counter-title">
                {isRTL ? `من أصل ${totalCount} وحدة مفعّلة` : `of ${totalCount} modules enabled`}
              </div>
              <div className="mc-counter-sub">
                {isRTL
                  ? `${ALWAYS_ENABLED_MODULES.length} ثابتة + ${VARIABLE_MODULES.filter(m => variableState[m]).length} متغيرة`
                  : `${ALWAYS_ENABLED_MODULES.length} fixed + ${VARIABLE_MODULES.filter(m => variableState[m]).length} variable`}
              </div>
            </div>
            <div className="mc-progress-wrap">
              <div className="mc-progress-bar">
                <div className="mc-progress-fill" style={{ width: `${progressPct}%` }} />
              </div>
            </div>
          </div>

          {/* Variable modules first */}
          <ModuleGroup
            title={isRTL ? '🔄 وحدات حسب نوع النشاط' : '🔄 Industry Modules'}
            description={isRTL ? 'قابلة للتفعيل والتعطيل حسب احتياجك' : 'Toggle based on your needs'}
            color={CATEGORY_LABELS['variable'].color}
            modules={grouped['variable'] || []}
            variableState={variableState}
            onToggle={handleToggle}
            isRTL={isRTL}
            locked={false}
          />

          {/* Fixed categories */}
          {['finance', 'sales', 'hr', 'core'].map(cat => (
            <ModuleGroup
              key={cat}
              title={isRTL ? CATEGORY_LABELS[cat].ar : CATEGORY_LABELS[cat].en}
              description={isRTL ? 'مفعّلة دائماً — لا يمكن تعطيلها' : 'Always enabled — cannot be disabled'}
              color={CATEGORY_LABELS[cat].color}
              modules={grouped[cat] || []}
              variableState={{}}
              onToggle={() => {}}
              isRTL={isRTL}
              locked={true}
            />
          ))}

          {error && <div className="mc-error">{error}</div>}

          {/* Footer */}
          <div className="mc-footer">
            <button className="mc-btn-skip" onClick={handleSkip}>
              {isRTL ? 'تخطي — استخدم الافتراضي' : 'Skip — Use Defaults'}
            </button>
            <button className="mc-btn-save" onClick={handleSave} disabled={saving}>
              {saving
                ? (isRTL ? '⏳ جاري الحفظ...' : '⏳ Saving...')
                : (isRTL
                    ? `✓ حفظ الإعدادات (${enabledCount} وحدة) والانطلاق`
                    : `✓ Save Settings (${enabledCount} modules) & Start`)}
            </button>
          </div>

        </div>
      </div>
    </>
  )
}

function ModuleGroup({ title, description, color, modules, variableState, onToggle, isRTL, locked }) {
  if (!modules.length) return null
  const onCount = locked ? modules.length : modules.filter(m => variableState[m.key]).length
  const borderSide = isRTL ? 'borderRight' : 'borderLeft'

  return (
    <div className="mc-group">
      <div className="mc-group-header" style={{ [borderSide]: `4px solid ${color}` }}>
        <div>
          <div className="mc-group-title">{title}</div>
          <div className="mc-group-desc">{description}</div>
        </div>
        <div className="mc-group-pill" style={{ background: `${color}15`, color, border: `1px solid ${color}30` }}>
          {locked
            ? `${modules.length} 🔒`
            : (isRTL ? `${onCount}/${modules.length} مفعّلة` : `${onCount}/${modules.length} enabled`)}
        </div>
      </div>

      <div className="mc-modules-grid">
        {modules.map(mod => {
          const isOn = locked ? true : (variableState[mod.key] ?? false)
          return (
            <div
              key={mod.key}
              className={`mc-module${locked ? ' locked' : ''}`}
              onClick={() => !locked && onToggle(mod.key)}
            >
              <div className="mc-module-icon-wrap" style={{ background: isOn ? `${color}15` : 'var(--bg-main, #f8fafc)' }}>
                {mod.icon}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div className="mc-module-name">{isRTL ? mod.ar : mod.en}</div>
                {locked && <div className="mc-module-sub">🔒 {isRTL ? 'ثابتة' : 'fixed'}</div>}
              </div>
              {!locked && (
                <div className="mc-toggle" style={{ background: isOn ? color : 'var(--border-color, #e2e8f0)' }}>
                  <div className="mc-toggle-knob" style={{ left: isOn ? '19px' : '3px' }} />
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default ModuleCustomization
