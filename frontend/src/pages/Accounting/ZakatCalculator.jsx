import { useState } from 'react'
import { zakatAPI } from '../../utils/api'
import { getCurrency, getCountry } from '../../utils/auth'
import { useTranslation } from 'react-i18next'
import { useToast } from '../../context/ToastContext'
import BackButton from '../../components/common/BackButton'
import { formatNumber } from '../../utils/format'
import { Clock } from 'lucide-react'

// Countries with full Zakat calculation support
const ZAKAT_SUPPORTED_COUNTRIES = ['SA']

const COUNTRY_FLAGS = {
    SA: '🇸🇦', SY: '🇸🇾', AE: '🇦🇪', EG: '🇪🇬', JO: '🇯🇴',
    KW: '🇰🇼', BH: '🇧🇭', OM: '🇴🇲', QA: '🇶🇦', IQ: '🇮🇶',
    LB: '🇱🇧', TR: '🇹🇷'
}

function ZakatCalculator() {
    const { t } = useTranslation()
    const { showToast } = useToast()
    const currency = getCurrency()
    const country = getCountry()
    const isSupported = ZAKAT_SUPPORTED_COUNTRIES.includes(country)
    const [fiscalYear, setFiscalYear] = useState(new Date().getFullYear())
    const [method, setMethod] = useState('net_assets')
    const [useGregorian, setUseGregorian] = useState(false)
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [posting, setPosting] = useState(false)

    const handleCalculate = async () => {
        setLoading(true)
        try {
            const res = await zakatAPI.calculate({
                fiscal_year: fiscalYear, method, use_gregorian_rate: useGregorian
            })
            setResult(res.data)
        } catch (err) {
            showToast(err.response?.data?.detail || t('common.error'), 'error')
        } finally { setLoading(false) }
    }

    const handlePost = async () => {
        setPosting(true)
        try {
            await zakatAPI.post(fiscalYear)
            showToast(t('zakat.posted_success'), 'success')
        } catch (err) {
            showToast(err.response?.data?.detail || t('common.error'), 'error')
        } finally { setPosting(false) }
    }

    // Show Coming Soon for unsupported countries
    if (!isSupported) {
        const flag = COUNTRY_FLAGS[country] || '🌍'
        return (
            <div className="workspace fade-in">
                <div className="workspace-header">
                    <BackButton />
                    <div className="header-title">
                        <h1 className="workspace-title">🕌 {t('zakat.title')}</h1>
                        <p className="workspace-subtitle">{t('zakat.subtitle')}</p>
                    </div>
                </div>

                <div className="card" style={{ padding: '60px 20px', textAlign: 'center' }}>
                    <div style={{ fontSize: '64px', marginBottom: '16px' }}>{flag}</div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', marginBottom: '12px' }}>
                        <Clock size={28} style={{ color: 'var(--text-muted)' }} />
                        <h2 style={{ fontSize: '28px', fontWeight: 700, color: 'var(--text-muted)' }}>
                            {t('coming_soon.title', 'قريباً')}
                        </h2>
                    </div>
                    <p style={{ color: 'var(--text-muted)', maxWidth: '480px', margin: '0 auto', lineHeight: 1.7 }}>
                        {t('zakat.coming_soon_country', 'حاسبة الزكاة غير متوفرة حالياً لدولتك. يعمل الفريق على دعم المزيد من الدول في التحديثات القادمة.')}
                    </p>
                </div>
            </div>
        )
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">🕌 {t('zakat.title')}</h1>
                    <p className="workspace-subtitle">{t('zakat.subtitle')}</p>
                </div>
            </div>

            <div className="alert alert-info mb-4">
                ℹ️ {t('zakat.islamic_note')}
            </div>

            <div className="card p-4">
                <div className="form-grid-4">
                    <div className="form-group">
                        <label>{t('zakat.fiscal_year')}</label>
                        <input type="number" className="form-input" value={fiscalYear} onChange={e => setFiscalYear(Number(e.target.value))} />
                    </div>
                    <div className="form-group">
                        <label>{t('zakat.method')}</label>
                        <select className="form-select" value={method} onChange={e => setMethod(e.target.value)}>
                            <option value="net_assets">{t('zakat.net_assets_method')}</option>
                            <option value="adjusted_profit">{t('zakat.adjusted_profit_method')}</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label>{t('zakat.year_type')}</label>
                        <div className="flex items-center gap-2 mt-2">
                            <input type="checkbox" id="gregorian" checked={useGregorian} onChange={e => setUseGregorian(e.target.checked)} />
                            <label htmlFor="gregorian">{t('zakat.use_gregorian')} (2.5775%)</label>
                        </div>
                    </div>
                    <div className="form-group" style={{ display: 'flex', alignItems: 'flex-end' }}>
                        <button className="btn btn-primary" onClick={handleCalculate} disabled={loading}>
                            {loading ? t('common.calculating') : t('zakat.calculate')}
                        </button>
                    </div>
                </div>
            </div>

            {result && (
                <>
                    {/* Zakat Base Details */}
                    <div className="grid grid-2 mt-4" style={{ gap: 16 }}>
                        <div className="card p-4">
                            <h3 className="card-title text-success mb-3">➕ {t('zakat.additions')}</h3>
                            {result.additions && result.additions.map((a, i) => (
                                <div key={i} className="flex justify-between py-1 border-bottom">
                                    <span>{a.label_ar || a.label}</span>
                                    <span className="font-medium">{formatNumber(a.amount)} {currency}</span>
                                </div>
                            ))}
                            <div className="flex justify-between py-2 font-bold mt-2">
                                <span>{t('zakat.total_additions')}</span>
                                <span className="text-success">{formatNumber(result.total_additions || 0)} {currency}</span>
                            </div>
                        </div>
                        <div className="card p-4">
                            <h3 className="card-title text-danger mb-3">➖ {t('zakat.deductions')}</h3>
                            {result.deductions && result.deductions.map((d, i) => (
                                <div key={i} className="flex justify-between py-1 border-bottom">
                                    <span>{d.label_ar || d.label}</span>
                                    <span className="font-medium">{formatNumber(d.amount)} {currency}</span>
                                </div>
                            ))}
                            <div className="flex justify-between py-2 font-bold mt-2">
                                <span>{t('zakat.total_deductions')}</span>
                                <span className="text-danger">{formatNumber(result.total_deductions || 0)} {currency}</span>
                            </div>
                        </div>
                    </div>

                    {/* Final Result */}
                    <div className="card mt-4 p-4">
                        <div className="grid grid-3" style={{ gap: 16, textAlign: 'center' }}>
                            <div>
                                <div className="text-muted">{t('zakat.zakat_base')}</div>
                                <div className="text-xl font-bold">{formatNumber(result.zakat_base)} {currency}</div>
                            </div>
                            <div>
                                <div className="text-muted">{t('zakat.rate')}</div>
                                <div className="text-xl font-bold">{result.rate || (useGregorian ? '2.5775%' : '2.5%')}</div>
                            </div>
                            <div>
                                <div className="text-muted">{t('zakat.zakat_amount')}</div>
                                <div className="text-2xl font-bold text-primary">{formatNumber(result.zakat_amount)} {currency}</div>
                            </div>
                        </div>

                        <div className="mt-4 flex justify-center">
                            <button className="btn btn-success" onClick={handlePost} disabled={posting}>
                                {posting ? t('common.posting') : `✅ ${t('zakat.post_journal_entry')}`}
                            </button>
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}

export default ZakatCalculator
