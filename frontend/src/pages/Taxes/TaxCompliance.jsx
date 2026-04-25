import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { taxComplianceAPI } from '../../utils/api'
import { useBranch } from '../../context/BranchContext'
import { useToast } from '../../context/ToastContext'
import { getCurrency } from '../../utils/auth'
import { formatNumber } from '../../utils/format'
import { formatShortDate } from '../../utils/dateUtils'
import { ShieldCheck, Globe, Building2, FileText, AlertTriangle, CheckCircle } from 'lucide-react'
import BackButton from '../../components/common/BackButton';
import { PageLoading, Spinner } from '../../components/common/LoadingStates'

const COUNTRY_FLAGS = {
    SA: '🇸🇦', SY: '🇸🇾', AE: '🇦🇪', EG: '🇪🇬', JO: '🇯🇴',
    KW: '🇰🇼', BH: '🇧🇭', OM: '🇴🇲', QA: '🇶🇦', IQ: '🇮🇶',
    LB: '🇱🇧', TR: '🇹🇷'
}

function TaxCompliance() {
    const { t, i18n } = useTranslation()
    const { showToast } = useToast()
    const { currentBranch } = useBranch()
    const currency = getCurrency()

    const [loading, setLoading] = useState(true)
    const [activeTab, setActiveTab] = useState('overview')
    const [overview, setOverview] = useState(null)
    const [countries, setCountries] = useState([])
    const [regimes, setRegimes] = useState([])
    const [companySettings, setCompanySettings] = useState(null)
    const [branchSettings, setBranchSettings] = useState(null)
    const [selectedCountry, setSelectedCountry] = useState('')
    const [reportData, setReportData] = useState(null)
    const [reportType, setReportType] = useState('')
    const [reportPeriod, setReportPeriod] = useState('')
    const [reportYear, setReportYear] = useState(new Date().getFullYear())
    const [reportLoading, setReportLoading] = useState(false)

    const fetchOverview = useCallback(async () => {
        try {
            setLoading(true)
            const [overviewRes, countriesRes] = await Promise.all([
                taxComplianceAPI.getOverview(),
                taxComplianceAPI.listCountries()
            ])
            setOverview(overviewRes.data)
            setCountries(overviewRes.data.countries || countriesRes.data)
        } catch (err) {
            console.error('Error fetching compliance overview:', err)
            showToast(err.response?.data?.detail || t('common.error', 'حدث خطأ في تحميل بيانات الامتثال'), 'error')
        } finally {
            setLoading(false)
        }
    }, [showToast, t])

    const fetchRegimes = useCallback(async (cc) => {
        try {
            const res = await taxComplianceAPI.listRegimes({ country_code: cc })
            setRegimes(res.data)
        } catch (err) {
            console.error('Error fetching regimes:', err)
            showToast(err.response?.data?.detail || t('common.error', 'حدث خطأ في تحميل الأنظمة الضريبية'), 'error')
        }
    }, [showToast, t])

    const fetchCompanySettings = useCallback(async () => {
        try {
            const res = await taxComplianceAPI.getCompanySettings()
            setCompanySettings(res.data)
        } catch (err) {
            console.error('Error fetching company settings:', err)
            showToast(err.response?.data?.detail || t('common.error', 'حدث خطأ في تحميل إعدادات الشركة'), 'error')
        }
    }, [showToast, t])

    const fetchBranchSettings = useCallback(async (branchId) => {
        try {
            const res = await taxComplianceAPI.getBranchSettings(branchId)
            setBranchSettings(res.data)
        } catch (err) {
            console.error('Error fetching branch settings:', err)
            showToast(err.response?.data?.detail || t('common.error', 'حدث خطأ في تحميل إعدادات الفرع'), 'error')
        }
    }, [showToast, t])

    useEffect(() => { fetchOverview() }, [fetchOverview])

    useEffect(() => {
        if (activeTab === 'regimes' && selectedCountry) fetchRegimes(selectedCountry)
    }, [activeTab, selectedCountry, fetchRegimes])

    useEffect(() => {
        if (activeTab === 'company') fetchCompanySettings()
    }, [activeTab, fetchCompanySettings])

    useEffect(() => {
        if (activeTab === 'branch' && currentBranch?.id) fetchBranchSettings(currentBranch.id)
    }, [activeTab, currentBranch, fetchBranchSettings])

    const handleGenerateReport = async () => {
        if (!reportType) return
        setReportLoading(true)
        setReportData(null)
        try {
            const params = { year: reportYear }
            if (reportPeriod) params.period = reportPeriod
            if (currentBranch?.id) params.branch_id = currentBranch.id

            let res
            switch (reportType) {
                case 'sa-vat':
                    res = await taxComplianceAPI.getSaudiVATReport(params)
                    break
                case 'sy-income':
                    res = await taxComplianceAPI.getSyrianIncomeReport(params)
                    break
                case 'ae-vat':
                    res = await taxComplianceAPI.getUAEVATReport(params)
                    break
                case 'eg-vat':
                    res = await taxComplianceAPI.getEgyptVATReport(params)
                    break
                default:
                    res = await taxComplianceAPI.getGenericIncomeReport(params)
            }
            setReportData(res.data)
        } catch (err) {
            console.error('Error generating report:', err)
            showToast(err.response?.data?.detail || t('common.error', 'حدث خطأ في توليد التقرير'), 'error')
        } finally {
            setReportLoading(false)
        }
    }



    if (loading && !overview) return <PageLoading />

    return (
        <div className="workspace fade-in">
            {/* Header */}
            <div className="workspace-header">
                <BackButton />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                    <div>
                        <h1 className="workspace-title"><ShieldCheck size={24} style={{ display: 'inline', marginInlineEnd: '8px' }} />{t('tax_compliance.title')}</h1>
                        <p className="workspace-subtitle">{t('tax_compliance.subtitle')}</p>
                    </div>
                </div>
            </div>

            {/* Summary Cards */}
            {overview && (
                <div className="metrics-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
                    <div className="metric-card">
                        <div className="metric-label"><Globe size={14} style={{ display: 'inline', marginInlineEnd: '4px' }} />{t('tax_compliance.jurisdictions')}</div>
                        <div className="metric-value">{overview.jurisdictions?.length || 0}</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-label"><FileText size={14} style={{ display: 'inline', marginInlineEnd: '4px' }} />{t('tax_compliance.active_regimes')}</div>
                        <div className="metric-value">{overview.countries_count || overview.jurisdictions?.length || 0}</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-label">{t('tax_compliance.pending_filings')}</div>
                        <div className="metric-value text-warning">{typeof overview.pending_returns === 'object' ? (overview.pending_returns?.draft || 0) + (overview.pending_returns?.overdue || 0) : (overview.pending_returns || 0)}</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-label"><Building2 size={14} style={{ display: 'inline', marginInlineEnd: '4px' }} />{t('tax_compliance.branches_configured')}</div>
                        <div className="metric-value">{overview.total_branches || 0}</div>
                    </div>
                </div>
            )}

            {/* Tabs */}
            <div className="tabs mt-4">
                {['overview', 'regimes', 'reports', 'company', 'branch'].map(tab => (
                    <button key={tab} className={`tab ${activeTab === tab ? 'active' : ''}`} onClick={() => setActiveTab(tab)}>
                        {t(`tax_compliance.tab_${tab}`)}
                    </button>
                ))}
            </div>

            {/* ── Overview Tab ── */}
            {activeTab === 'overview' && overview && (
                <div className="mt-4">
                    {/* Jurisdictions */}
                    <div className="card mb-4">
                        <h3 className="section-title">{t('tax_compliance.active_jurisdictions')}</h3>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '12px', marginTop: '12px' }}>
                            {(overview.jurisdictions || []).map(j => (
                                <div key={j.country_code} className="card" style={{ padding: '16px', border: '1px solid var(--border)' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                        <span style={{ fontSize: '24px' }}>{COUNTRY_FLAGS[j.country_code] || '🏳️'}</span>
                                        <div>
                                            <strong>{i18n.language === 'ar' ? j.name_ar : j.name_en}</strong>
                                            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{j.country_code}</div>
                                        </div>
                                    </div>
                                    <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                                        {j.tax_types?.join(', ') || [j.has_vat && 'VAT', j.has_zakat && 'Zakat'].filter(Boolean).join(', ') || t('tax_compliance.no_taxes_configured')}
                                    </div>
                                </div>
                            ))}
                            {(!overview.jurisdictions || overview.jurisdictions.length === 0) && (
                                <p className="text-muted">{t('tax_compliance.no_jurisdictions')}</p>
                            )}
                        </div>
                    </div>

                    {/* Branch Status */}
                    <div className="card">
                        <h3 className="section-title">{t('tax_compliance.branch_compliance_status')}</h3>
                        <div className="table-container mt-3">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>{t('tax_compliance.branch_name')}</th>
                                        <th>{t('tax_compliance.country')}</th>
                                        <th>{t('tax_compliance.configured_taxes')}</th>
                                        <th>{t('tax_compliance.registered_taxes')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {(overview.jurisdictions || []).flatMap(j =>
                                        (j.branches || []).map(b => (
                                            <tr key={`${j.country_code}-${b.id}`}>
                                                <td>{b.name || b.branch_name}</td>
                                                <td>{COUNTRY_FLAGS[j.country_code] || ''} {j.country_code}</td>
                                                <td>{b.configured_taxes || 0}</td>
                                                <td>{b.registered_taxes || 0}</td>
                                            </tr>
                                        ))
                                    )}
                                    {(!overview.jurisdictions || overview.jurisdictions.flatMap(j => j.branches || []).length === 0) && (
                                        <tr><td colSpan={4} className="text-muted text-center">{t('tax_compliance.no_branches')}</td></tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}

            {/* ── Tax Regimes Tab ── */}
            {activeTab === 'regimes' && (
                <div className="mt-4">
                    <div className="card mb-4">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                            <label style={{ fontWeight: 600 }}>{t('tax_compliance.filter_by_country')}:</label>
                            <select
                                value={selectedCountry}
                                onChange={(e) => setSelectedCountry(e.target.value)}
                                className="form-input"
                                style={{ maxWidth: '250px' }}
                            >
                                <option value="">{t('tax_compliance.select_country')}</option>
                                {(countries || []).map(c => (
                                    <option key={c.code || c.country_code} value={c.code || c.country_code}>
                                        {COUNTRY_FLAGS[c.code || c.country_code]} {i18n.language === 'ar' ? c.name_ar : c.name_en}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {selectedCountry && (
                            <div className="table-container">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>{t('tax_compliance.tax_type')}</th>
                                            <th>{t(i18n.language === 'ar' ? 'tax_compliance.name_ar' : 'tax_compliance.name_en')}</th>
                                            <th>{t('tax_compliance.default_rate')}</th>
                                            <th>{t('tax_compliance.required')}</th>
                                            <th>{t('tax_compliance.applies_to')}</th>
                                            <th>{t('tax_compliance.filing_freq')}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {regimes.map(r => (
                                            <tr key={r.id}>
                                                <td><code style={{ padding: '2px 6px', background: 'var(--bg-secondary)', borderRadius: '4px', fontSize: '12px' }}>{r.tax_type}</code></td>
                                                <td>{i18n.language === 'ar' ? r.name_ar : r.name_en}</td>
                                                <td style={{ fontWeight: 600 }}>{r.default_rate}%</td>
                                                <td>{r.is_required ?
                                                    <span style={{ color: 'var(--error)', fontWeight: 600 }}>✓ {t('tax_compliance.mandatory')}</span> :
                                                    <span style={{ color: 'var(--text-muted)' }}>{t('tax_compliance.optional')}</span>
                                                }</td>
                                                <td>{t(`tax_compliance.applies_${r.applies_to}`) || r.applies_to}</td>
                                                <td>{t(`tax_compliance.freq_${r.filing_frequency}`) || r.filing_frequency}</td>
                                            </tr>
                                        ))}
                                        {regimes.length === 0 && (
                                            <tr><td colSpan={6} className="text-muted text-center">{t('tax_compliance.no_regimes')}</td></tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* ── Reports Tab ── */}
            {activeTab === 'reports' && (
                <div className="mt-4">
                    <div className="card mb-4">
                        <h3 className="section-title">{t('tax_compliance.generate_report')}</h3>
                        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '12px', alignItems: 'flex-end' }}>
                            <div>
                                <label className="form-label">{t('tax_compliance.report_type')}</label>
                                <select value={reportType} onChange={e => { setReportType(e.target.value); setReportData(null) }}
                                    className="form-input" style={{ minWidth: '220px' }}>
                                    <option value="">{t('tax_compliance.select_report')}</option>
                                    {(companySettings && (Array.isArray(companySettings) ? companySettings : [companySettings]).some(cs => cs.country_code === 'SA')) && (
                                        <option value="sa-vat">🇸🇦 {t('tax_compliance.report_sa_vat')}</option>
                                    )}
                                    <option value="sy-income">🇸🇾 {t('tax_compliance.report_sy_income')}</option>
                                    <option value="ae-vat">🇦🇪 {t('tax_compliance.report_ae_vat')}</option>
                                    <option value="eg-vat">🇪🇬 {t('tax_compliance.report_eg_vat')}</option>
                                    <option value="generic-income">🌐 {t('tax_compliance.report_generic_income')}</option>
                                </select>
                            </div>
                            <div>
                                <label className="form-label">{t('tax_compliance.year')}</label>
                                <input type="number" value={reportYear} onChange={e => setReportYear(parseInt(e.target.value))}
                                    className="form-input" style={{ width: '120px' }} min={2020} max={2030} />
                            </div>
                            <div>
                                <label className="form-label">{t('tax_compliance.period')}</label>
                                <input type="text" value={reportPeriod} onChange={e => setReportPeriod(e.target.value)}
                                    className="form-input" style={{ width: '150px' }} placeholder="Q1, Q2, 01, 02..." />
                            </div>
                            <button className="btn btn-primary" onClick={handleGenerateReport} disabled={!reportType || reportLoading}>
                                {reportLoading ? <Spinner size="sm"/> : <FileText size={16} />}
                                {' '}{t('tax_compliance.generate')}
                            </button>
                        </div>
                    </div>

                    {/* Report Output */}
                    {reportData && (
                        <div className="card">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                                <h3 className="section-title" style={{ margin: 0 }}>{reportData.report_name || reportData.title}</h3>
                                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                                    {t('tax_compliance.generated_at')}: {formatShortDate(reportData.generated_at || new Date().toISOString())}
                                </span>
                            </div>

                            {/* Report header info */}
                            {reportData.company_name && (
                                <div style={{ background: 'var(--bg-secondary)', padding: '12px 16px', borderRadius: '8px', marginBottom: '16px' }}>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '13px' }}>
                                        <div><strong>{t('tax_compliance.company')}:</strong> {reportData.company_name}</div>
                                        {reportData.tax_number && <div><strong>{t('tax_compliance.tax_number')}:</strong> {reportData.tax_number}</div>}
                                        {reportData.period && <div><strong>{t('tax_compliance.period')}:</strong> {reportData.period}</div>}
                                        {reportData.currency && <div><strong>{t('tax_compliance.currency')}:</strong> {reportData.currency}</div>}
                                    </div>
                                </div>
                            )}

                            {/* Boxes / Line items */}
                            {reportData.boxes && (
                                <div className="table-container">
                                    <table className="data-table">
                                        <thead>
                                            <tr>
                                                <th style={{ width: '60px' }}>#</th>
                                                <th>{t('tax_compliance.description')}</th>
                                                <th style={{ width: '150px', textAlign: 'end' }}>{t('tax_compliance.taxable_amount')}</th>
                                                <th style={{ width: '150px', textAlign: 'end' }}>{t('tax_compliance.tax_amount')}</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {reportData.boxes.map((box, i) => (
                                                <tr key={i} style={box.is_total ? { fontWeight: 700, background: 'var(--bg-secondary)' } : {}}>
                                                    <td>{box.box_number || box.number || (i + 1)}</td>
                                                    <td>{i18n.language === 'ar' ? (box.description_ar || box.description) : (box.description_en || box.description)}</td>
                                                    <td style={{ textAlign: 'end' }}>{box.taxable_amount != null ? formatNumber(box.taxable_amount) : '—'}</td>
                                                    <td style={{ textAlign: 'end' }}>{box.tax_amount != null ? formatNumber(box.tax_amount) : (box.amount != null ? formatNumber(box.amount) : '—')}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}

                            {/* Summary totals */}
                            {reportData.summary && (
                                <div style={{ marginTop: '16px', padding: '16px', background: 'var(--bg-secondary)', borderRadius: '8px' }}>
                                    <h4 style={{ margin: '0 0 12px' }}>{t('tax_compliance.summary')}</h4>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
                                        {Object.entries(reportData.summary).map(([key, val]) => (
                                            <div key={key}>
                                                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{t(`tax_compliance.summary_${key}`) || key.replace(/_/g, ' ')}</div>
                                                <div style={{ fontSize: '18px', fontWeight: 700 }}>{typeof val === 'number' ? formatNumber(val) : val}</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* ── Company Settings Tab ── */}
            {activeTab === 'company' && companySettings && (
                <div className="mt-4">
                    <div className="card">
                        <h3 className="section-title">{t('tax_compliance.company_tax_settings')}</h3>
                        <div className="table-container mt-3">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>{t('tax_compliance.country')}</th>
                                        <th>{t('tax_compliance.tax_number')}</th>
                                        <th>{t('tax_compliance.fiscal_year_start')}</th>
                                        <th>{t('tax_compliance.is_active')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {(Array.isArray(companySettings) ? companySettings : [companySettings]).map((cs, i) => (
                                        <tr key={i}>
                                            <td>{COUNTRY_FLAGS[cs.country_code]} {cs.country_code}</td>
                                            <td>{cs.tax_registration_number || '—'}</td>
                                            <td>{cs.fiscal_year_start || '01-01'}</td>
                                            <td>{cs.is_active ? <CheckCircle size={16} style={{ color: 'var(--success)' }} /> : '—'}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}

            {/* ── Branch Settings Tab ── */}
            {activeTab === 'branch' && (
                <div className="mt-4">
                    <div className="card">
                        <h3 className="section-title">
                            <Building2 size={18} style={{ display: 'inline', marginInlineEnd: '8px' }} />
                            {t('tax_compliance.branch_tax_settings')}
                            {currentBranch && <span style={{ fontWeight: 400, fontSize: '14px', color: 'var(--text-muted)', marginInlineStart: '8px' }}>— {currentBranch.name}</span>}
                        </h3>
                        {!currentBranch ? (
                            <p className="text-muted mt-3">{t('tax_compliance.select_branch_first')}</p>
                        ) : branchSettings ? (
                            <div className="mt-3">
                                <div style={{ background: 'var(--bg-secondary)', padding: '12px 16px', borderRadius: '8px', marginBottom: '16px' }}>
                                    <strong>{t('tax_compliance.jurisdiction')}:</strong> {COUNTRY_FLAGS[branchSettings.jurisdiction] || ''} {branchSettings.jurisdiction}
                                </div>
                                <div className="table-container">
                                    <table className="data-table">
                                        <thead>
                                            <tr>
                                                <th>{t('tax_compliance.regime')}</th>
                                                <th>{t('tax_compliance.effective_rate')}</th>
                                                <th>{t('tax_compliance.is_active')}</th>
                                                <th>{t('tax_compliance.registration_number')}</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {(branchSettings.settings || branchSettings.regimes || []).map((s, i) => (
                                                <tr key={i}>
                                                    <td>{i18n.language === 'ar' ? s.name_ar : s.name_en}</td>
                                                    <td style={{ fontWeight: 600 }}>{s.effective_rate ?? s.override_rate ?? s.default_rate}%</td>
                                                    <td>{s.is_active ? <CheckCircle size={16} style={{ color: 'var(--success)' }} /> : '—'}</td>
                                                    <td>{s.registration_number || '—'}</td>
                                                </tr>
                                            ))}
                                            {(!branchSettings.settings?.length && !branchSettings.regimes?.length) && (
                                                <tr><td colSpan={4} className="text-muted text-center">{t('tax_compliance.no_branch_settings')}</td></tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        ) : (
                            <PageLoading />
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}

export default TaxCompliance
