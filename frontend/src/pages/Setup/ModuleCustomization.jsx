import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ALWAYS_ENABLED_MODULES, VARIABLE_MODULES, INDUSTRY_TYPES, getEnabledModulesForIndustry } from '../../config/industryModules'
import { getIndustryType } from '../../hooks/useIndustryType'
import { getUser, updateUser } from '../../utils/auth'
import api from '../../services/apiClient'

// ===== تعريف كامل لجميع الوحدات =====
const MODULE_LABELS = {
  // الوحدات الثابتة (17)
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
  // الوحدات المتغيرة (5)
  pos:           { ar: 'نقاط البيع',          en: 'Point of Sale',   icon: '🏪', category: 'variable' },
  stock:         { ar: 'المخزون',             en: 'Inventory',       icon: '📦', category: 'variable' },
  manufacturing: { ar: 'التصنيع',             en: 'Manufacturing',   icon: '🏭', category: 'variable' },
  projects:      { ar: 'المشاريع',            en: 'Projects',        icon: '📐', category: 'variable' },
  services:      { ar: 'الخدمات والصيانة',    en: 'Services',        icon: '🔧', category: 'variable' },
}

const CATEGORY_LABELS = {
  core:     { ar: 'وحدات أساسية',    en: 'Core Modules',        color: '#3b82f6' },
  finance:  { ar: 'المالية والمحاسبة', en: 'Finance',            color: '#8b5cf6' },
  sales:    { ar: 'المبيعات والتسويق', en: 'Sales & CRM',        color: '#06b6d4' },
  hr:       { ar: 'الموارد البشرية',  en: 'Human Resources',     color: '#f59e0b' },
  variable: { ar: 'وحدات حسب النشاط', en: 'Industry Modules',   color: '#10b981' },
}

function ModuleCustomization() {
  const { i18n } = useTranslation()
  const navigate = useNavigate()
  const isRTL = i18n.language === 'ar'

  // قراءة نوع النشاط المختار
  const industryKey = getIndustryType()
  const industry = industryKey ? INDUSTRY_TYPES[industryKey] : null

  // قراءة الوحدات من user object (ما حفظه IndustrySetup)
  const user = getUser()
  const initialEnabled = user?.enabled_modules || (industryKey ? getEnabledModulesForIndustry(industryKey) : [])

  // state للوحدات المتغيرة فقط (الثابتة لا تتغير)
  const [variableState, setVariableState] = useState(() => {
    const state = {}
    VARIABLE_MODULES.forEach(m => {
      state[m] = initialEnabled.includes(m)
    })
    return state
  })

  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  // الوحدات النهائية المفعّلة
  const finalModules = [
    ...ALWAYS_ENABLED_MODULES,
    ...VARIABLE_MODULES.filter(m => variableState[m]),
  ]

  const enabledCount = finalModules.length
  const totalCount = ALWAYS_ENABLED_MODULES.length + VARIABLE_MODULES.length

  const handleToggle = (moduleKey) => {
    if (ALWAYS_ENABLED_MODULES.includes(moduleKey)) return // مقفلة
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

  const handleSkip = () => {
    window.location.href = '/dashboard'
  }

  // تجميع الوحدات حسب الفئة
  const grouped = {}
  Object.entries(MODULE_LABELS).forEach(([key, label]) => {
    const cat = label.category
    if (!grouped[cat]) grouped[cat] = []
    grouped[cat].push({ key, ...label })
  })

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '40px 20px',
      direction: isRTL ? 'rtl' : 'ltr',
    }}>
      {/* ===== HEADER ===== */}
      <div style={{
        width: '100%',
        maxWidth: '900px',
        marginBottom: '32px',
      }}>
        {/* زر الرجوع */}
        <button
          onClick={() => navigate('/setup/industry')}
          style={{
            background: 'rgba(255,255,255,0.1)',
            border: '1px solid rgba(255,255,255,0.2)',
            color: 'white',
            padding: '8px 16px',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '14px',
            marginBottom: '24px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          {isRTL ? '← تغيير نوع النشاط' : '← Change Business Type'}
        </button>

        {/* Industry badge */}
        {industry && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '16px',
            background: 'rgba(59, 130, 246, 0.15)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            borderRadius: '16px',
            padding: '16px 24px',
            marginBottom: '24px',
          }}>
            <div style={{ fontSize: '40px' }}>{industry.icon}</div>
            <div>
              <div style={{ color: '#93c5fd', fontSize: '13px', marginBottom: '4px' }}>
                {isRTL ? 'نوع النشاط المختار' : 'Selected Business Type'}
              </div>
              <div style={{ color: 'white', fontSize: '20px', fontWeight: '700' }}>
                {isRTL ? industry.nameAr : industry.nameEn}
              </div>
              <div style={{ color: '#94a3b8', fontSize: '13px' }}>
                {isRTL ? industry.descriptionAr : industry.descriptionEn}
              </div>
            </div>
          </div>
        )}

        {/* العنوان */}
        <div>
          <h1 style={{
            color: 'white',
            fontSize: '28px',
            fontWeight: '800',
            marginBottom: '8px',
          }}>
            {isRTL ? '⚙️ تخصيص الوحدات' : '⚙️ Customize Modules'}
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '15px' }}>
            {isRTL
              ? 'الوحدات الثابتة مُفعَّلة دائماً ومُقفَلة. يمكنك تفعيل أو تعطيل الوحدات المتغيرة حسب احتياجك.'
              : 'Core modules are always enabled and locked. Toggle variable modules based on your needs.'}
          </p>
        </div>
      </div>

      {/* ===== COUNTER BAR ===== */}
      <div style={{
        width: '100%',
        maxWidth: '900px',
        background: 'rgba(255,255,255,0.05)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: '12px',
        padding: '16px 24px',
        marginBottom: '24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #22c55e, #16a34a)',
            color: 'white',
            fontWeight: '800',
            fontSize: '20px',
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            {enabledCount}
          </div>
          <div>
            <div style={{ color: 'white', fontWeight: '700', fontSize: '16px' }}>
              {isRTL ? `من أصل ${totalCount} وحدة مفعّلة` : `of ${totalCount} modules enabled`}
            </div>
            <div style={{ color: '#94a3b8', fontSize: '13px' }}>
              {isRTL
                ? `${ALWAYS_ENABLED_MODULES.length} ثابتة + ${VARIABLE_MODULES.filter(m => variableState[m]).length} متغيرة`
                : `${ALWAYS_ENABLED_MODULES.length} fixed + ${VARIABLE_MODULES.filter(m => variableState[m]).length} variable`}
            </div>
          </div>
        </div>

        {/* Progress bar */}
        <div style={{ flex: 1, minWidth: '200px' }}>
          <div style={{
            background: 'rgba(255,255,255,0.1)',
            borderRadius: '999px',
            height: '8px',
            overflow: 'hidden',
          }}>
            <div style={{
              width: `${(enabledCount / totalCount) * 100}%`,
              height: '100%',
              background: 'linear-gradient(90deg, #3b82f6, #22c55e)',
              borderRadius: '999px',
              transition: 'width 0.3s ease',
            }} />
          </div>
        </div>
      </div>

      {/* ===== MODULE GROUPS ===== */}
      <div style={{ width: '100%', maxWidth: '900px' }}>

        {/* 1. الوحدات المتغيرة أولاً (الأهم للمستخدم) */}
        <ModuleGroup
          title={isRTL ? '🔄 وحدات حسب نوع النشاط (قابلة للتغيير)' : '🔄 Industry Modules (Customizable)'}
          description={isRTL ? 'يمكنك تفعيل أو تعطيل هذه الوحدات حسب احتياجك' : 'Toggle these modules based on your needs'}
          color="#10b981"
          modules={grouped['variable'] || []}
          variableState={variableState}
          onToggle={handleToggle}
          isRTL={isRTL}
          locked={false}
        />

        {/* 2. الفئات الثابتة */}
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
      </div>

      {/* ===== ERROR ===== */}
      {error && (
        <div style={{
          width: '100%',
          maxWidth: '900px',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#fca5a5',
          padding: '12px 20px',
          borderRadius: '10px',
          marginTop: '16px',
          textAlign: 'center',
        }}>
          {error}
        </div>
      )}

      {/* ===== FOOTER BUTTONS ===== */}
      <div style={{
        width: '100%',
        maxWidth: '900px',
        marginTop: '32px',
        display: 'flex',
        gap: '12px',
        flexWrap: 'wrap',
      }}>
        <button
          onClick={handleSkip}
          style={{
            flex: 1,
            minWidth: '140px',
            background: 'rgba(255,255,255,0.08)',
            border: '1px solid rgba(255,255,255,0.15)',
            color: '#94a3b8',
            padding: '16px',
            borderRadius: '12px',
            fontSize: '15px',
            fontWeight: '600',
            cursor: 'pointer',
          }}
        >
          {isRTL ? 'تخطي — استخدم الافتراضي' : 'Skip — Use Defaults'}
        </button>

        <button
          onClick={handleSave}
          disabled={saving}
          style={{
            flex: 3,
            minWidth: '200px',
            background: saving
              ? 'rgba(59, 130, 246, 0.5)'
              : 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
            color: 'white',
            padding: '16px',
            borderRadius: '12px',
            border: 'none',
            fontSize: '17px',
            fontWeight: '700',
            cursor: saving ? 'wait' : 'pointer',
            boxShadow: '0 10px 25px -5px rgba(59, 130, 246, 0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
          }}
        >
          {saving
            ? (isRTL ? '⏳ جاري الحفظ...' : '⏳ Saving...')
            : (isRTL ? `✓ حفظ الإعدادات (${enabledCount} وحدة) والانطلاق` : `✓ Save Settings (${enabledCount} modules) & Start`)
          }
        </button>
      </div>

      <div style={{ height: '60px' }} />
    </div>
  )
}

// ===== مكوّن مجموعة الوحدات =====
function ModuleGroup({ title, description, color, modules, variableState, onToggle, isRTL, locked }) {
  if (!modules.length) return null

  return (
    <div style={{
      marginBottom: '24px',
      background: 'rgba(255,255,255,0.03)',
      border: `1px solid ${color}30`,
      borderRadius: '16px',
      overflow: 'hidden',
    }}>
      {/* Group header */}
      <div style={{
        background: `${color}15`,
        borderBottom: `1px solid ${color}25`,
        padding: '16px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '12px',
      }}>
        <div>
          <div style={{ color: 'white', fontWeight: '700', fontSize: '16px' }}>{title}</div>
          <div style={{ color: '#94a3b8', fontSize: '13px', marginTop: '2px' }}>{description}</div>
        </div>
        <div style={{
          background: `${color}20`,
          border: `1px solid ${color}40`,
          color: color,
          padding: '4px 12px',
          borderRadius: '999px',
          fontSize: '13px',
          fontWeight: '700',
          whiteSpace: 'nowrap',
        }}>
          {locked
            ? (isRTL ? `${modules.length} ثابتة 🔒` : `${modules.length} fixed 🔒`)
            : (() => {
                const onCount = modules.filter(m => variableState[m.key]).length
                return isRTL ? `${onCount}/${modules.length} مفعّلة` : `${onCount}/${modules.length} enabled`
              })()
          }
        </div>
      </div>

      {/* Module cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
        gap: '1px',
        background: 'rgba(255,255,255,0.05)',
      }}>
        {modules.map(mod => {
          const isOn = locked ? true : (variableState[mod.key] ?? false)
          return (
            <div
              key={mod.key}
              onClick={() => !locked && onToggle(mod.key)}
              style={{
                background: isOn
                  ? `${color}10`
                  : 'rgba(15,23,42,0.8)',
                padding: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                cursor: locked ? 'default' : 'pointer',
                transition: 'background 0.2s ease',
                position: 'relative',
              }}
            >
              {/* الأيقونة */}
              <div style={{
                width: '36px',
                height: '36px',
                background: isOn ? `${color}20` : 'rgba(255,255,255,0.05)',
                borderRadius: '10px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '18px',
                flexShrink: 0,
                transition: 'background 0.2s',
              }}>
                {mod.icon}
              </div>

              {/* الاسم */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                  color: isOn ? 'white' : '#64748b',
                  fontWeight: '600',
                  fontSize: '13px',
                  lineHeight: '1.4',
                  transition: 'color 0.2s',
                }}>
                  {isRTL ? mod.ar : mod.en}
                </div>
                {locked && (
                  <div style={{ fontSize: '10px', color: '#475569', marginTop: '2px' }}>
                    {isRTL ? '🔒 ثابتة' : '🔒 fixed'}
                  </div>
                )}
              </div>

              {/* Toggle switch */}
              {!locked && (
                <div style={{
                  width: '36px',
                  height: '20px',
                  background: isOn ? color : '#1e293b',
                  border: `1px solid ${isOn ? color : '#334155'}`,
                  borderRadius: '999px',
                  position: 'relative',
                  transition: 'background 0.2s, border-color 0.2s',
                  flexShrink: 0,
                }}>
                  <div style={{
                    width: '14px',
                    height: '14px',
                    background: 'white',
                    borderRadius: '50%',
                    position: 'absolute',
                    top: '2px',
                    left: isOn ? '18px' : '2px',
                    transition: 'left 0.2s ease',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
                  }} />
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
