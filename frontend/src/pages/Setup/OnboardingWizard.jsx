import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { getIndustryTypesList, getEnabledModulesForIndustry, ALWAYS_ENABLED_MODULES, VARIABLE_MODULES, INDUSTRY_TYPES } from '../../config/industryModules'
import { useIndustryType } from '../../hooks/useIndustryType'
import { getUser, updateUser, getCompanyId } from '../../utils/auth'
import api from '../../services/apiClient'

const COUNTRY_DEFAULTS = {
  SA: { currency: 'SAR', timezone: 'Asia/Riyadh' },
  SY: { currency: 'SYP', timezone: 'Asia/Damascus' },
  AE: { currency: 'AED', timezone: 'Asia/Dubai' },
  EG: { currency: 'EGP', timezone: 'Africa/Cairo' },
  KW: { currency: 'KWD', timezone: 'Asia/Kuwait' },
  TR: { currency: 'TRY', timezone: 'Europe/Istanbul' },
}

const TOTAL_STEPS = 4

function OnboardingWizard() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const { setIndustryType } = useIndustryType()
  const isRTL = i18n.language === 'ar'
  const user = getUser()
  const companyId = getCompanyId()

  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Step 1: Company details
  const userCountry = user?.country || 'SA'
  const defaults = COUNTRY_DEFAULTS[userCountry] || COUNTRY_DEFAULTS.SA
  const [companyInfo, setCompanyInfo] = useState({
    company_name_en: '',
    phone: '',
    address: '',
    commercial_registry: '',
    tax_number: '',
    currency: user?.currency || defaults.currency,
    timezone: user?.timezone || defaults.timezone,
  })

  // Step 2: Industry selection
  const [selectedIndustry, setSelectedIndustry] = useState(null)
  const industries = getIndustryTypesList()

  // Step 3: Module customization
  const [moduleOverrides, setModuleOverrides] = useState({})

  const enabledModules = useMemo(() => {
    if (!selectedIndustry) return [...ALWAYS_ENABLED_MODULES]
    const base = getEnabledModulesForIndustry(selectedIndustry)
    // Apply user overrides for variable modules
    return base.map(m => {
      if (VARIABLE_MODULES.includes(m) && moduleOverrides[m] === false) return null
      return m
    }).filter(Boolean).concat(
      VARIABLE_MODULES.filter(m => !base.includes(m) && moduleOverrides[m] === true)
    )
  }, [selectedIndustry, moduleOverrides])

  const toggleModule = (key) => {
    if (!VARIABLE_MODULES.includes(key)) return
    setModuleOverrides(prev => {
      const base = selectedIndustry ? getEnabledModulesForIndustry(selectedIndustry) : []
      const isCurrentlyEnabled = enabledModules.includes(key)
      return { ...prev, [key]: !isCurrentlyEnabled }
    })
  }

  const MODULE_LABELS = {
    dashboard: { icon: '🏠' }, kpi: { icon: '📊' }, accounting: { icon: '📒' },
    assets: { icon: '🏗️' }, treasury: { icon: '🏦' }, sales: { icon: '💰' },
    buying: { icon: '🛒' }, crm: { icon: '🤝' }, expenses: { icon: '💸' },
    taxes: { icon: '🧾' }, approvals: { icon: '✅' }, reports: { icon: '📈' },
    hr: { icon: '👥' }, audit: { icon: '📋' }, roles: { icon: '🔐' },
    settings: { icon: '⚙️' }, data_import: { icon: '📥' },
    pos: { icon: '🏪' }, stock: { icon: '📦' }, manufacturing: { icon: '🏭' },
    projects: { icon: '📐' }, services: { icon: '🔧' },
  }

  const getModuleName = (key) => {
    const nameMap = {
      dashboard: t('nav.dashboard'), kpi: t('nav.kpi_dashboards'), accounting: t('nav.accounting'),
      assets: t('nav.assets'), treasury: t('reports_center.groups.treasury'), sales: t('reports.tables.sales'),
      buying: t('nav.buying'), crm: t('nav.crm'), expenses: t('projects.tabs.expenses'),
      taxes: t('nav.taxes'), approvals: t('nav.approvals'), reports: t('common.reports'),
      hr: t('nav.hr'), audit: t('audit.title'), roles: t('nav.roles'),
      settings: t('common.settings'), data_import: t('nav.dataImport'),
      pos: t('nav.pos'), stock: t('nav.inventory'), manufacturing: t('manufacturing.title'),
      projects: t('reports.tables.projects'), services: t('nav.services'),
    }
    return nameMap[key] || key
  }

  const toggleLanguage = () => i18n.changeLanguage(isRTL ? 'en' : 'ar')

  const handleCompanyInfoChange = (e) => {
    const { name, value } = e.target
    setCompanyInfo(prev => ({ ...prev, [name]: value }))
  }

  const goNext = () => {
    setError('')
    if (step === 2 && !selectedIndustry) {
      setError(t('onboarding.select_industry_error', 'يرجى اختيار نوع النشاط'))
      return
    }
    setStep(s => Math.min(s + 1, TOTAL_STEPS))
  }

  const goBack = () => {
    setError('')
    setStep(s => Math.max(s - 1, 1))
  }

  const handleConfirm = async () => {
    setLoading(true)
    setError('')
    try {
      // 1. Save company info (optional fields)
      const infoToSave = {}
      if (companyInfo.company_name_en) infoToSave.company_name_en = companyInfo.company_name_en
      if (companyInfo.phone) infoToSave.phone = companyInfo.phone
      if (companyInfo.address) infoToSave.address = companyInfo.address
      if (companyInfo.commercial_registry) infoToSave.commercial_registry = companyInfo.commercial_registry
      if (companyInfo.tax_number) infoToSave.tax_number = companyInfo.tax_number

      if (Object.keys(infoToSave).length > 0 && companyId) {
        try {
          await api.put(`/companies/update/${companyId}`, infoToSave)
        } catch (err) {
          console.warn('Company info update failed (non-blocking):', err)
        }
      }

      // 2. Save currency/timezone settings
      await api.post('/settings/bulk', {
        settings: {
          currency: companyInfo.currency,
          timezone: companyInfo.timezone,
        }
      })

      // 3. Save industry type (this also saves modules)
      const success = await setIndustryType(selectedIndustry)
      if (!success) {
        setError(t('onboarding.save_failed', 'فشل حفظ الإعدادات، يرجى المحاولة مرة أخرى'))
        setLoading(false)
        return
      }

      // 4. If user customized modules, save the override
      if (Object.keys(moduleOverrides).length > 0) {
        try {
          await api.put('/companies/modules', enabledModules)
          updateUser({ enabled_modules: enabledModules })
        } catch (err) {
          console.warn('Module override save failed (non-blocking):', err)
        }
      }

      // Update user with currency/timezone
      updateUser({
        currency: companyInfo.currency,
        timezone: companyInfo.timezone,
      })

      // 5. Navigate to dashboard
      window.location.href = '/dashboard'
    } catch (err) {
      setError(err.response?.data?.detail || t('onboarding.save_failed', 'فشل حفظ الإعدادات'))
      setLoading(false)
    }
  }

  const selectedIndustryData = selectedIndustry ? industries.find(i => i.key === selectedIndustry) : null

  const STEP_CONFIG = [
    { num: 1, icon: '🏢', label: t('onboarding.step_company', 'معلومات الشركة') },
    { num: 2, icon: '🏭', label: t('onboarding.step_industry', 'نوع النشاط') },
    { num: 3, icon: '⚙️', label: t('onboarding.step_modules', 'الوحدات') },
    { num: 4, icon: '✅', label: t('onboarding.step_confirm', 'تأكيد') },
  ]

  return (
    <>
      <style>{`
        .onboard-layout {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--bg-main, #f8fafc);
          padding: 24px 16px;
          direction: ${isRTL ? 'rtl' : 'ltr'};
        }
        .onboard-card {
          background: var(--bg-card, #fff);
          padding: 36px 32px;
          border-radius: 16px;
          box-shadow: var(--shadow-lg, 0 10px 15px -3px rgba(0,0,0,0.1));
          border: 1px solid var(--border-color, #e2e8f0);
          width: 100%;
          max-width: ${step === 2 ? '960px' : step === 3 ? '800px' : '640px'};
          transition: max-width 0.35s ease;
          animation: wizFadeUp 0.35s ease-out;
        }
        .onboard-lang-btn {
          position: fixed;
          top: 16px;
          ${isRTL ? 'left' : 'right'}: 16px;
          z-index: 50;
        }
        .onboard-header {
          text-align: center;
          margin-bottom: 24px;
        }
        .onboard-header h1 {
          font-size: 22px;
          font-weight: 700;
          color: var(--text-main, #1e293b);
          margin-bottom: 6px;
        }
        .onboard-header p {
          font-size: 14px;
          color: var(--text-secondary, #64748b);
        }

        /* Stepper */
        .onboard-stepper {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 4px;
          margin-bottom: 28px;
          flex-wrap: wrap;
        }
        .onboard-step {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 4px 0;
        }
        .onboard-step-dot {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 14px;
          font-weight: 700;
          transition: all 0.3s;
        }
        .onboard-step-dot.active { background: var(--primary, #2563eb); color: #fff; }
        .onboard-step-dot.done { background: var(--success, #10b981); color: #fff; }
        .onboard-step-dot.pending { background: #f1f5f9; color: var(--text-muted, #94a3b8); }
        .onboard-step-text {
          font-size: 12px;
          font-weight: 600;
          color: var(--text-secondary, #64748b);
        }
        .onboard-step-text.active { color: var(--primary, #2563eb); }
        .onboard-step-line {
          width: 32px;
          height: 2px;
          border-radius: 1px;
          margin: 0 4px;
        }

        /* Industry Grid */
        .onboard-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
          gap: 10px;
          margin-bottom: 24px;
        }
        .onboard-ind {
          position: relative;
          background: var(--bg-card, #fff);
          border: 2px solid var(--border-color, #e2e8f0);
          border-radius: 12px;
          padding: 18px 12px;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
          gap: 6px;
        }
        .onboard-ind:hover {
          background: var(--bg-hover, #f1f5f9);
          border-color: var(--primary-light, #60a5fa);
          transform: translateY(-2px);
        }
        .onboard-ind.selected {
          background: #eff6ff;
          border-color: var(--primary, #2563eb);
          box-shadow: 0 4px 12px -4px rgba(37,99,235,0.25);
          transform: translateY(-2px);
        }
        .onboard-ind-icon {
          width: 44px; height: 44px; border-radius: 10px;
          background: #f1f5f9;
          display: flex; align-items: center; justify-content: center;
          font-size: 22px; transition: all 0.2s;
        }
        .onboard-ind.selected .onboard-ind-icon {
          background: var(--primary, #2563eb);
          box-shadow: 0 4px 10px -2px rgba(37,99,235,0.3);
        }
        .onboard-ind-name { font-weight: 700; font-size: 13px; color: var(--text-main, #1e293b); }
        .onboard-ind.selected .onboard-ind-name { color: var(--primary, #2563eb); }
        .onboard-ind-desc { font-size: 11px; color: var(--text-muted, #94a3b8); line-height: 1.4; }
        .onboard-ind-check {
          position: absolute; top: 6px; ${isRTL ? 'left' : 'right'}: 6px;
          background: var(--primary, #2563eb); color: #fff;
          width: 20px; height: 20px; border-radius: 50%;
          display: flex; align-items: center; justify-content: center;
          font-size: 11px; font-weight: bold;
          animation: wizScaleIn 0.2s ease;
        }

        /* Modules */
        .onboard-mods-section { margin-bottom: 16px; }
        .onboard-mods-label {
          font-size: 12px; font-weight: 700;
          color: var(--text-muted, #94a3b8);
          text-transform: uppercase; letter-spacing: 1px;
          margin-bottom: 8px;
          display: flex; align-items: center; gap: 10px;
        }
        .onboard-mods-label::after {
          content: ''; flex: 1; height: 1px; background: var(--border-color, #e2e8f0);
        }
        .onboard-mods-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(165px, 1fr));
          gap: 8px;
        }
        .onboard-mod {
          display: flex; align-items: center; gap: 8px;
          padding: 8px 12px; border-radius: 8px;
          font-size: 13px; border: 1px solid; transition: all 0.15s;
        }
        .onboard-mod.on { background: #f0fdf4; border-color: #bbf7d0; color: #166534; cursor: pointer; }
        .onboard-mod.off { background: #fef2f2; border-color: #fecaca; color: var(--text-muted, #94a3b8); cursor: pointer; }
        .onboard-mod.core { background: #f8fafc; border-color: var(--border-color, #e2e8f0); color: var(--text-secondary, #64748b); }
        .onboard-mod.on:hover, .onboard-mod.off:hover { transform: translateY(-1px); box-shadow: var(--shadow-sm); }
        .onboard-mod-icon { font-size: 16px; flex-shrink: 0; }
        .onboard-mod-name { flex: 1; font-weight: 600; font-size: 12px; }
        .onboard-mod-badge { font-size: 14px; flex-shrink: 0; }

        /* Summary */
        .onboard-summary {
          background: var(--bg-hover, #f8fafc);
          border: 1px solid var(--border-color, #e2e8f0);
          border-radius: 12px;
          padding: 20px;
          margin-bottom: 20px;
        }
        .onboard-summary-row {
          display: flex; justify-content: space-between; align-items: center;
          padding: 8px 0;
          border-bottom: 1px solid var(--border-color, #e2e8f0);
        }
        .onboard-summary-row:last-child { border-bottom: none; }
        .onboard-summary-label { font-size: 13px; color: var(--text-secondary, #64748b); }
        .onboard-summary-value { font-size: 13px; font-weight: 600; color: var(--text-main, #1e293b); }
        .onboard-summary-mods {
          display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px;
        }
        .onboard-summary-mod-tag {
          background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px;
          padding: 3px 8px; font-size: 11px; font-weight: 600; color: var(--primary, #2563eb);
        }

        .onboard-note {
          background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px;
          padding: 10px 16px; margin-bottom: 16px;
          font-size: 13px; color: #92400e; text-align: center;
        }
        .onboard-btn-row { display: flex; gap: 10px; }

        @keyframes wizScaleIn { from { transform: scale(0); opacity: 0; } to { transform: scale(1); opacity: 1; } }
        @keyframes wizFadeUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        @media (max-width: 600px) {
          .onboard-card { padding: 20px 16px; }
          .onboard-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); }
          .onboard-mods-grid { grid-template-columns: 1fr 1fr; }
          .onboard-step-text { display: none; }
          .onboard-header h1 { font-size: 18px; }
        }
      `}</style>

      <div className="onboard-layout">
        <div className="onboard-lang-btn">
          <button className="btn btn-outline btn-sm" onClick={toggleLanguage}>
            {isRTL ? 'EN' : 'AR'}
          </button>
        </div>

        <div className="onboard-card">
          {/* Header */}
          <div className="onboard-header">
            <h1>{t('onboarding.title', 'إعداد نظامك')}</h1>
            <p>{t('onboarding.subtitle', 'أكمل الخطوات التالية لتخصيص النظام حسب احتياجاتك')}</p>
          </div>

          {/* Stepper */}
          <div className="onboard-stepper">
            {STEP_CONFIG.map((s, i) => (
              <div key={s.num} style={{ display: 'flex', alignItems: 'center' }}>
                <div className="onboard-step">
                  <div className={`onboard-step-dot ${step > s.num ? 'done' : step === s.num ? 'active' : 'pending'}`}>
                    {step > s.num ? '✓' : s.num}
                  </div>
                  <span className={`onboard-step-text ${step === s.num ? 'active' : ''}`}>
                    {s.label}
                  </span>
                </div>
                {i < STEP_CONFIG.length - 1 && (
                  <div className="onboard-step-line" style={{ background: step > s.num ? 'var(--success, #10b981)' : '#e2e8f0' }} />
                )}
              </div>
            ))}
          </div>

          {error && <div className="alert alert-error" style={{ marginBottom: 16 }}>{error}</div>}

          {/* ─── Step 1: Company Details ─── */}
          {step === 1 && (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '20px' }}>
                <div className="form-group">
                  <label className="form-label">{t('auth.company_name_en', 'اسم الشركة (إنجليزي)')}</label>
                  <input type="text" name="company_name_en" className="form-input"
                    placeholder="e.g. Company Name" value={companyInfo.company_name_en} onChange={handleCompanyInfoChange} />
                </div>
                <div className="form-group">
                  <label className="form-label">{t('auth.phone', 'الهاتف')}</label>
                  <input type="tel" name="phone" className="form-input"
                    placeholder="+966 5x xxx xxxx" value={companyInfo.phone} onChange={handleCompanyInfoChange} />
                </div>
                <div className="form-group" style={{ gridColumn: 'span 2' }}>
                  <label className="form-label">{t('onboarding.address', 'العنوان')}</label>
                  <input type="text" name="address" className="form-input"
                    placeholder={t('onboarding.address_placeholder', 'عنوان الشركة')} value={companyInfo.address} onChange={handleCompanyInfoChange} />
                </div>
                <div className="form-group">
                  <label className="form-label">{t('onboarding.commercial_registry', 'السجل التجاري')}</label>
                  <input type="text" name="commercial_registry" className="form-input"
                    placeholder={t('onboarding.cr_placeholder', 'رقم السجل التجاري')} value={companyInfo.commercial_registry} onChange={handleCompanyInfoChange} />
                </div>
                <div className="form-group">
                  <label className="form-label">{t('onboarding.tax_number', 'الرقم الضريبي')}</label>
                  <input type="text" name="tax_number" className="form-input"
                    placeholder={t('onboarding.tax_placeholder', 'الرقم الضريبي (VAT)')} value={companyInfo.tax_number} onChange={handleCompanyInfoChange} />
                </div>
                <div className="form-group">
                  <label className="form-label">{t('auth.currency', 'العملة')}</label>
                  <select name="currency" className="form-input" value={companyInfo.currency} onChange={handleCompanyInfoChange}>
                    <option value="SAR">{t('auth.register.sar', 'ريال سعودي')}</option>
                    <option value="SYP">{t('auth.register.syp', 'ليرة سورية')}</option>
                    <option value="USD">{t('auth.register.usd', 'دولار أمريكي')}</option>
                    <option value="AED">{t('auth.register.aed', 'درهم إماراتي')}</option>
                    <option value="EGP">{t('auth.register.egp', 'جنيه مصري')}</option>
                    <option value="KWD">{t('auth.register.kwd', 'دينار كويتي')}</option>
                    <option value="TRY">{t('auth.register.try_currency', 'ليرة تركية')}</option>
                    <option value="EUR">{t('auth.register.eur', 'يورو')}</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">{t('auth.timezone', 'المنطقة الزمنية')}</label>
                  <select name="timezone" className="form-input" value={companyInfo.timezone} onChange={handleCompanyInfoChange}>
                    <option value="Asia/Riyadh">{t('timezones.riyadh', 'الرياض')}</option>
                    <option value="Asia/Damascus">{t('timezones.damascus', 'دمشق')}</option>
                    <option value="Asia/Dubai">{t('timezones.dubai', 'دبي')}</option>
                    <option value="Africa/Cairo">{t('timezones.cairo', 'القاهرة')}</option>
                    <option value="Asia/Kuwait">{t('timezones.kuwait', 'الكويت')}</option>
                    <option value="Europe/Istanbul">{t('timezones.istanbul', 'إسطنبول')}</option>
                    <option value="UTC">UTC</option>
                  </select>
                </div>
              </div>

              <div className="onboard-note">
                {t('onboarding.step1_note', 'يمكنك تخطي هذه الخطوة وإكمال المعلومات لاحقاً من الإعدادات')}
              </div>

              <div className="onboard-btn-row">
                <button className="btn btn-primary btn-block" onClick={goNext}>
                  {t('onboarding.next', 'التالي')} →
                </button>
              </div>
            </>
          )}

          {/* ─── Step 2: Industry Selection ─── */}
          {step === 2 && (
            <>
              <div className="onboard-grid">
                {industries.map(ind => (
                  <div
                    key={ind.key}
                    className={`onboard-ind ${selectedIndustry === ind.key ? 'selected' : ''}`}
                    onClick={() => { setSelectedIndustry(ind.key); setModuleOverrides({}); setError('') }}
                  >
                    <div className="onboard-ind-icon">{ind.icon}</div>
                    <div className="onboard-ind-name">
                      {isRTL ? ind.nameAr : ind.nameEn}
                    </div>
                    <div className="onboard-ind-desc">
                      {isRTL ? ind.descriptionAr : ind.descriptionEn}
                    </div>
                    {selectedIndustry === ind.key && (
                      <div className="onboard-ind-check">✓</div>
                    )}
                  </div>
                ))}
              </div>

              <div className="onboard-btn-row">
                <button className="btn btn-secondary" onClick={goBack} style={{ flex: 1 }}>
                  ← {t('onboarding.back', 'رجوع')}
                </button>
                <button className="btn btn-primary" onClick={goNext} disabled={!selectedIndustry} style={{ flex: 2 }}>
                  {t('onboarding.next', 'التالي')} →
                </button>
              </div>
            </>
          )}

          {/* ─── Step 3: Module Customization ─── */}
          {step === 3 && (
            <>
              {selectedIndustryData && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 12, padding: '12px 16px', marginBottom: 20 }}>
                  <span style={{ fontSize: 28 }}>{selectedIndustryData.icon}</span>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--primary, #2563eb)' }}>
                      {isRTL ? selectedIndustryData.nameAr : selectedIndustryData.nameEn}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary, #64748b)' }}>
                      {t('onboarding.customize_modules_desc', 'يمكنك تفعيل أو تعطيل الوحدات المتغيرة حسب حاجتك')}
                    </div>
                  </div>
                </div>
              )}

              {/* Variable Modules (toggleable) */}
              <div className="onboard-mods-section">
                <div className="onboard-mods-label">
                  {t('onboarding.variable_modules', 'وحدات متغيرة (انقر للتبديل)')}
                </div>
                <div className="onboard-mods-grid">
                  {VARIABLE_MODULES.map(key => {
                    const isOn = enabledModules.includes(key)
                    return (
                      <div key={key} className={`onboard-mod ${isOn ? 'on' : 'off'}`} onClick={() => toggleModule(key)}>
                        <span className="onboard-mod-icon">{MODULE_LABELS[key]?.icon}</span>
                        <span className="onboard-mod-name">{getModuleName(key)}</span>
                        <span className="onboard-mod-badge">{isOn ? '✅' : '❌'}</span>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Core Modules (always on) */}
              <div className="onboard-mods-section">
                <div className="onboard-mods-label">
                  {t('onboarding.core_modules', 'وحدات أساسية (مفعّلة دائماً)')}
                </div>
                <div className="onboard-mods-grid">
                  {ALWAYS_ENABLED_MODULES.map(key => (
                    <div key={key} className="onboard-mod core">
                      <span className="onboard-mod-icon">{MODULE_LABELS[key]?.icon}</span>
                      <span className="onboard-mod-name">{getModuleName(key)}</span>
                      <span className="onboard-mod-badge">✅</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="onboard-note">
                {t('onboarding.modules_note', 'يمكنك تعديل الوحدات المفعّلة لاحقاً من الإعدادات')}
              </div>

              <div className="onboard-btn-row">
                <button className="btn btn-secondary" onClick={goBack} style={{ flex: 1 }}>
                  ← {t('onboarding.back', 'رجوع')}
                </button>
                <button className="btn btn-primary" onClick={goNext} style={{ flex: 2 }}>
                  {t('onboarding.next', 'التالي')} →
                </button>
              </div>
            </>
          )}

          {/* ─── Step 4: Summary & Confirm ─── */}
          {step === 4 && (
            <>
              <div className="onboard-summary">
                {companyInfo.company_name_en && (
                  <div className="onboard-summary-row">
                    <span className="onboard-summary-label">{t('auth.company_name_en', 'اسم الشركة (إنجليزي)')}</span>
                    <span className="onboard-summary-value">{companyInfo.company_name_en}</span>
                  </div>
                )}
                <div className="onboard-summary-row">
                  <span className="onboard-summary-label">{t('auth.currency', 'العملة')}</span>
                  <span className="onboard-summary-value">{companyInfo.currency}</span>
                </div>
                <div className="onboard-summary-row">
                  <span className="onboard-summary-label">{t('auth.timezone', 'المنطقة الزمنية')}</span>
                  <span className="onboard-summary-value">{companyInfo.timezone}</span>
                </div>
                {selectedIndustryData && (
                  <div className="onboard-summary-row">
                    <span className="onboard-summary-label">{t('onboarding.step_industry', 'نوع النشاط')}</span>
                    <span className="onboard-summary-value">
                      {selectedIndustryData.icon} {isRTL ? selectedIndustryData.nameAr : selectedIndustryData.nameEn}
                    </span>
                  </div>
                )}
                {companyInfo.commercial_registry && (
                  <div className="onboard-summary-row">
                    <span className="onboard-summary-label">{t('onboarding.commercial_registry', 'السجل التجاري')}</span>
                    <span className="onboard-summary-value">{companyInfo.commercial_registry}</span>
                  </div>
                )}
                {companyInfo.tax_number && (
                  <div className="onboard-summary-row">
                    <span className="onboard-summary-label">{t('onboarding.tax_number', 'الرقم الضريبي')}</span>
                    <span className="onboard-summary-value">{companyInfo.tax_number}</span>
                  </div>
                )}
              </div>

              {/* Active Modules Summary */}
              <div style={{ marginBottom: 20 }}>
                <div className="onboard-mods-label">
                  {t('onboarding.active_modules', 'الوحدات المفعّلة')} ({enabledModules.length})
                </div>
                <div className="onboard-summary-mods">
                  {enabledModules.map(key => (
                    <span key={key} className="onboard-summary-mod-tag">
                      {MODULE_LABELS[key]?.icon} {getModuleName(key)}
                    </span>
                  ))}
                </div>
              </div>

              <div className="onboard-btn-row">
                <button className="btn btn-secondary" onClick={goBack} style={{ flex: 1 }}>
                  ← {t('onboarding.back', 'رجوع')}
                </button>
                <button className="btn btn-success" onClick={handleConfirm} disabled={loading} style={{ flex: 2 }}>
                  {loading
                    ? t('onboarding.saving', 'جاري الحفظ...')
                    : t('onboarding.confirm_start', '✓ تأكيد وبدء العمل')
                  }
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  )
}

export default OnboardingWizard
