import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { accountingAPI } from '../../utils/api'
import { useToast } from '../../context/ToastContext'
import CustomDatePicker from '../../components/common/CustomDatePicker'

export default function ClosingEntries() {
    const { t, i18n } = useTranslation()
    const { showToast } = useToast()
    const isAr = i18n.language === 'ar'

    const now = new Date()
    const [startDate, setStartDate] = useState(`${now.getFullYear()}-01-01`)
    const [endDate, setEndDate] = useState(now.toISOString().slice(0, 10))
    const [loading, setLoading] = useState(false)
    const [generating, setGenerating] = useState(false)
    const [preview, setPreview] = useState(null)
    const [useIncomeSummary, setUseIncomeSummary] = useState(false)
    const [result, setResult] = useState(null)

    const fetchPreview = async () => {
        setLoading(true)
        setResult(null)
        try {
            const res = await accountingAPI.previewClosingEntries({ start_date: startDate, end_date: endDate })
            setPreview(res.data)
        } catch (err) {
            showToast(err.response?.data?.detail || 'Error', 'error')
        } finally {
            setLoading(false)
        }
    }

    const handleGenerate = async () => {
        if (!confirm(isAr ? 'هل أنت متأكد من توليد قيود الإقفال؟ سيتم ترحيلها مباشرة.' : 'Generate and post closing entries?'))
            return
        setGenerating(true)
        try {
            const payload = {
                start_date: startDate,
                end_date: endDate,
                entry_date: endDate,
                use_income_summary: useIncomeSummary,
                income_summary_account_id: preview?.income_summary_account?.id,
                retained_earnings_account_id: preview?.retained_earnings_account?.id,
            }
            const res = await accountingAPI.generateClosingEntries(payload)
            setResult(res.data)
            showToast(res.data.message || (isAr ? 'تم التوليد' : 'Generated'), 'success')
            setPreview(null)
        } catch (err) {
            showToast(err.response?.data?.detail || 'Error', 'error')
        } finally {
            setGenerating(false)
        }
    }

    const formatNum = (n) => {
        if (!n && n !== 0) return '-'
        return parseFloat(n).toLocaleString('en', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }

    return (
        <div className="workspace fade-in" dir={isAr ? 'rtl' : 'ltr'}>
            <div className="workspace-header">
                <div>
                    <h1 className="workspace-title">🔒 {isAr ? 'قيود الإقفال التلقائي' : 'Automatic Closing Entries'}</h1>
                    <p className="workspace-subtitle">
                        {isAr
                            ? 'إقفال حسابات الإيرادات والمصاريف وترحيل صافي الدخل إلى الأرباح المبقاة'
                            : 'Close revenue and expense accounts and transfer net income to retained earnings'}
                    </p>
                </div>
            </div>

            {/* Period Selection */}
            <div className="card border-0 shadow-sm mb-4" style={{ borderRadius: '12px' }}>
                <div className="card-body p-4">
                    <h5 className="fw-bold mb-3">📅 {isAr ? 'اختيار الفترة' : 'Select Period'}</h5>
                    <div className="row g-3">
                        <div className="col-md-4">
                            <CustomDatePicker
                                label={isAr ? 'من تاريخ' : 'Start Date'}
                                selected={startDate}
                                onChange={(dateStr) => setStartDate(dateStr)}
                            />
                        </div>
                        <div className="col-md-4">
                            <CustomDatePicker
                                label={isAr ? 'إلى تاريخ' : 'End Date'}
                                selected={endDate}
                                onChange={(dateStr) => setEndDate(dateStr)}
                            />
                        </div>
                        <div className="col-md-4">
                            <label className="form-label" style={{ opacity: 0 }}>.</label>
                            <button className="btn btn-primary w-100" onClick={fetchPreview} disabled={loading}>
                                {loading ? '⏳' : '🔍'} {isAr ? 'معاينة' : 'Preview'}
                            </button>
                        </div>
                    </div>
                    <div className="mt-3">
                        <div className="form-check">
                            <input type="checkbox" className="form-check-input" id="useIS"
                                checked={useIncomeSummary} onChange={e => setUseIncomeSummary(e.target.checked)} />
                            <label className="form-check-label" htmlFor="useIS">
                                {isAr ? 'استخدام ملخص الدخل' : 'Use Income Summary Account'}
                            </label>
                        </div>
                    </div>
                </div>
            </div>

            {/* Result of generation */}
            {result && (
                <div className="card border-0 shadow-sm mb-4" style={{ borderRadius: '12px', borderLeft: '4px solid #10b981' }}>
                    <div className="card-body p-4">
                        <h5 className="fw-bold text-success mb-3">✅ {result.message}</h5>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '16px' }}>
                            <div className="p-3 bg-light rounded text-center">
                                <div className="small text-muted">{isAr ? 'إجمالي الإيرادات' : 'Total Revenue'}</div>
                                <div className="fw-bold text-success fs-5">{formatNum(result.total_revenue)}</div>
                            </div>
                            <div className="p-3 bg-light rounded text-center">
                                <div className="small text-muted">{isAr ? 'إجمالي المصاريف' : 'Total Expenses'}</div>
                                <div className="fw-bold text-danger fs-5">{formatNum(result.total_expense)}</div>
                            </div>
                            <div className="p-3 bg-light rounded text-center">
                                <div className="small text-muted">{isAr ? 'صافي الدخل' : 'Net Income'}</div>
                                <div className={`fw-bold fs-5 ${result.net_income >= 0 ? 'text-success' : 'text-danger'}`}>
                                    {formatNum(result.net_income)}
                                </div>
                            </div>
                        </div>
                        <div className="mt-3">
                            <strong>{isAr ? 'القيود المولدة:' : 'Generated Entries:'}</strong>{' '}
                            <span className="badge bg-primary">{result.entries.map(e => `#${e.number}`).join(', ')}</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Preview */}
            {preview && (
                <>
                    {/* Summary Cards */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                        <div className="card p-3 text-center border-success">
                            <div className="fs-4 mb-2">📈</div>
                            <div className="small text-muted">{isAr ? 'إجمالي الإيرادات' : 'Total Revenue'}</div>
                            <div className="fw-bold fs-4 text-success">{formatNum(preview.total_revenue)}</div>
                            <div className="small text-muted">{preview.revenues.length} {isAr ? 'حساب' : 'accounts'}</div>
                        </div>
                        <div className="card p-3 text-center border-danger">
                            <div className="fs-4 mb-2">📉</div>
                            <div className="small text-muted">{isAr ? 'إجمالي المصاريف' : 'Total Expenses'}</div>
                            <div className="fw-bold fs-4 text-danger">{formatNum(preview.total_expense)}</div>
                            <div className="small text-muted">{preview.expenses.length} {isAr ? 'حساب' : 'accounts'}</div>
                        </div>
                        <div className={`card p-3 text-center border-${preview.net_income >= 0 ? 'success' : 'warning'}`}>
                            <div className="fs-4 mb-2">{preview.net_income >= 0 ? '💰' : '⚠️'}</div>
                            <div className="small text-muted">{isAr ? 'صافي الدخل' : 'Net Income'}</div>
                            <div className={`fw-bold fs-4 ${preview.net_income >= 0 ? 'text-success' : 'text-warning'}`}>
                                {formatNum(preview.net_income)}
                            </div>
                            <div className="small text-muted">
                                {preview.net_income >= 0 ? (isAr ? 'ربح' : 'Profit') : (isAr ? 'خسارة' : 'Loss')}
                            </div>
                        </div>
                    </div>

                    {/* Target Accounts */}
                    <div className="card border-0 shadow-sm mb-4" style={{ borderRadius: '12px' }}>
                        <div className="card-body p-4">
                            <h6 className="fw-bold mb-3">🎯 {isAr ? 'الحسابات المستهدفة' : 'Target Accounts'}</h6>
                            <div className="row g-3">
                                <div className="col-md-6">
                                    <label className="form-label small text-muted">{isAr ? 'حساب الأرباح المبقاة' : 'Retained Earnings Account'}</label>
                                    <div className="form-input" style={{ background: '#f8f9fa' }}>
                                        {preview.retained_earnings_account
                                            ? `${preview.retained_earnings_account.account_number} - ${preview.retained_earnings_account.name}`
                                            : <span className="text-danger">❌ {isAr ? 'غير موجود!' : 'Not found!'}</span>}
                                    </div>
                                </div>
                                {useIncomeSummary && (
                                    <div className="col-md-6">
                                        <label className="form-label small text-muted">{isAr ? 'حساب ملخص الدخل' : 'Income Summary Account'}</label>
                                        <div className="form-input" style={{ background: '#f8f9fa' }}>
                                            {preview.income_summary_account
                                                ? `${preview.income_summary_account.account_number} - ${preview.income_summary_account.name}`
                                                : <span className="text-warning">⚠️ {isAr ? 'غير موجود' : 'Not found'}</span>}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Revenue Accounts Table */}
                    {preview.revenues.length > 0 && (
                        <div className="card border-0 shadow-sm mb-4" style={{ borderRadius: '12px' }}>
                            <div className="card-header bg-success bg-opacity-10 border-0" style={{ borderRadius: '12px 12px 0 0' }}>
                                <strong className="text-success">📈 {isAr ? 'حسابات الإيرادات' : 'Revenue Accounts'}</strong>
                            </div>
                            <div className="data-table-container">
                                <table className="data-table mb-0">
                                    <thead>
                                        <tr>
                                            <th>{isAr ? 'رقم' : 'Code'}</th>
                                            <th>{isAr ? 'الحساب' : 'Account'}</th>
                                            <th className="text-end">{isAr ? 'الرصيد' : 'Balance'}</th>
                                            <th className="text-end">{isAr ? 'مدين (إقفال)' : 'Debit (Close)'}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {preview.revenues.map(r => (
                                            <tr key={r.id}>
                                                <td className="text-muted small">{r.account_number}</td>
                                                <td>{isAr ? r.name : (r.name_en || r.name)}</td>
                                                <td className="text-end text-success">{formatNum(r.balance)}</td>
                                                <td className="text-end">{formatNum(r.balance)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                    <tfoot className="fw-bold">
                                        <tr>
                                            <td colSpan="2">{isAr ? 'الإجمالي' : 'Total'}</td>
                                            <td className="text-end text-success">{formatNum(preview.total_revenue)}</td>
                                            <td className="text-end">{formatNum(preview.total_revenue)}</td>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Expense Accounts Table */}
                    {preview.expenses.length > 0 && (
                        <div className="card border-0 shadow-sm mb-4" style={{ borderRadius: '12px' }}>
                            <div className="card-header bg-danger bg-opacity-10 border-0" style={{ borderRadius: '12px 12px 0 0' }}>
                                <strong className="text-danger">📉 {isAr ? 'حسابات المصاريف' : 'Expense Accounts'}</strong>
                            </div>
                            <div className="data-table-container">
                                <table className="data-table mb-0">
                                    <thead>
                                        <tr>
                                            <th>{isAr ? 'رقم' : 'Code'}</th>
                                            <th>{isAr ? 'الحساب' : 'Account'}</th>
                                            <th className="text-end">{isAr ? 'الرصيد' : 'Balance'}</th>
                                            <th className="text-end">{isAr ? 'دائن (إقفال)' : 'Credit (Close)'}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {preview.expenses.map(e => (
                                            <tr key={e.id}>
                                                <td className="text-muted small">{e.account_number}</td>
                                                <td>{isAr ? e.name : (e.name_en || e.name)}</td>
                                                <td className="text-end text-danger">{formatNum(e.balance)}</td>
                                                <td className="text-end">{formatNum(e.balance)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                    <tfoot className="fw-bold">
                                        <tr>
                                            <td colSpan="2">{isAr ? 'الإجمالي' : 'Total'}</td>
                                            <td className="text-end text-danger">{formatNum(preview.total_expense)}</td>
                                            <td className="text-end">{formatNum(preview.total_expense)}</td>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Generate Button */}
                    <div className="text-center mt-4">
                        <button className="btn btn-danger btn-lg px-5" onClick={handleGenerate}
                            disabled={generating || (!preview.revenues.length && !preview.expenses.length)}
                            style={{ borderRadius: '8px' }}>
                            {generating ? '⏳' : '🔒'}{' '}
                            {isAr ? 'توليد قيود الإقفال وترحيلها' : 'Generate & Post Closing Entries'}
                        </button>
                        <p className="text-muted small mt-2">
                            {isAr ? 'سيتم ترحيل القيود مباشرة بعد التوليد' : 'Entries will be posted immediately'}
                        </p>
                    </div>
                </>
            )}

            {!preview && !result && !loading && (
                <div className="card border-0 shadow-sm text-center p-5" style={{ borderRadius: '12px' }}>
                    <div style={{ fontSize: '72px', marginBottom: '16px' }}>🔒</div>
                    <h5 className="fw-bold mb-2">{isAr ? 'قيود الإقفال التلقائي' : 'Automatic Closing Entries'}</h5>
                    <p className="text-muted">{isAr ? 'حدد الفترة ثم اضغط "معاينة" لمعاينة قيود الإقفال' : 'Select a period and click "Preview" to view closing entries'}</p>
                </div>
            )}
        </div>
    )
}
