import { useState, useEffect, useCallback } from 'react'
import { externalAPI } from '../../utils/api'
import { formatNumber } from '../../utils/format'
import { getCurrency } from '../../utils/auth'
import '../../components/ModuleStyles.css'

export default function WithholdingTax() {
    const currency = getCurrency()
    const [activeTab, setActiveTab] = useState('rates')
    const [loading, setLoading] = useState(true)

    // Rates state
    const [rates, setRates] = useState([])
    const [showRateModal, setShowRateModal] = useState(false)
    const [rateForm, setRateForm] = useState({ name: '', name_ar: '', rate: '', category: 'services' })
    const [rateSubmitting, setRateSubmitting] = useState(false)

    // Transactions state
    const [transactions, setTransactions] = useState([])
    const [txLoading, setTxLoading] = useState(false)

    // Calculator state
    const [calcRateId, setCalcRateId] = useState('')
    const [calcGross, setCalcGross] = useState('')
    const [calcResult, setCalcResult] = useState(null)
    const [calcLoading, setCalcLoading] = useState(false)
    const [txSubmitting, setTxSubmitting] = useState(false)

    const categoryLabels = {
        services: 'خدمات',
        rent: 'إيجار',
        royalties: 'إتاوات',
        consulting: 'استشارات',
        other: 'أخرى',
    }

    const fetchRates = useCallback(async () => {
        try {
            setLoading(true)
            const res = await externalAPI.listWhtRates()
            setRates(res.data ?? res)
        } catch (e) {
            console.error(e)
        } finally {
            setLoading(false)
        }
    }, [])

    const fetchTransactions = useCallback(async () => {
        try {
            setTxLoading(true)
            const res = await externalAPI.listWhtTransactions()
            setTransactions(res.data ?? res)
        } catch (e) {
            console.error(e)
        } finally {
            setTxLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchRates()
    }, [fetchRates])

    useEffect(() => {
        if (activeTab === 'transactions') {
            fetchTransactions()
            if (rates.length === 0) fetchRates()
        }
    }, [activeTab, fetchTransactions, fetchRates, rates.length])

    const handleCreateRate = async (e) => {
        e.preventDefault()
        try {
            setRateSubmitting(true)
            await externalAPI.createWhtRate({
                ...rateForm,
                rate: parseFloat(rateForm.rate),
            })
            setShowRateModal(false)
            setRateForm({ name: '', name_ar: '', rate: '', category: 'services' })
            fetchRates()
        } catch (e) {
            console.error(e)
            alert('حدث خطأ أثناء إنشاء النسبة')
        } finally {
            setRateSubmitting(false)
        }
    }

    const handleCalculate = async () => {
        if (!calcRateId || !calcGross) return
        try {
            setCalcLoading(true)
            const res = await externalAPI.calculateWht({
                wht_rate_id: parseInt(calcRateId),
                gross_amount: parseFloat(calcGross),
            })
            setCalcResult(res.data ?? res)
        } catch (e) {
            console.error(e)
            alert('حدث خطأ أثناء الحساب')
        } finally {
            setCalcLoading(false)
        }
    }

    const handleCreateTransaction = async () => {
        if (!calcResult) return
        try {
            setTxSubmitting(true)
            await externalAPI.createWhtTransaction({
                wht_rate_id: parseInt(calcRateId),
                gross_amount: parseFloat(calcGross),
                ...calcResult,
            })
            setCalcResult(null)
            setCalcRateId('')
            setCalcGross('')
            fetchTransactions()
        } catch (e) {
            console.error(e)
            alert('حدث خطأ أثناء إنشاء المعاملة')
        } finally {
            setTxSubmitting(false)
        }
    }

    const formatDate = (d) => {
        if (!d) return '—'
        return new Date(d).toLocaleDateString('ar-EG', { year: 'numeric', month: 'short', day: 'numeric' })
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div className="header-title">
                    <h1 className="workspace-title">ضريبة الاستقطاع</h1>
                    <p className="workspace-subtitle">إدارة نسب ومعاملات ضريبة الاستقطاع (WHT)</p>
                </div>
                {activeTab === 'rates' && (
                    <div className="header-actions">
                        <button className="btn btn-primary" onClick={() => setShowRateModal(true)}>
                            + إضافة نسبة
                        </button>
                    </div>
                )}
            </div>

            {/* Tabs */}
            <div className="tabs-container" style={{ marginBottom: '24px' }}>
                <button
                    className={`tab-btn ${activeTab === 'rates' ? 'active' : ''}`}
                    onClick={() => setActiveTab('rates')}
                >
                    النسب
                </button>
                <button
                    className={`tab-btn ${activeTab === 'transactions' ? 'active' : ''}`}
                    onClick={() => setActiveTab('transactions')}
                >
                    المعاملات
                </button>
            </div>

            {/* ===== Rates Tab ===== */}
            {activeTab === 'rates' && (
                <div className="section-card">
                    {loading ? (
                        <div className="page-center"><span className="loading"></span></div>
                    ) : rates.length === 0 ? (
                        <div className="empty-state">
                            <p>لا توجد نسب استقطاع بعد</p>
                        </div>
                    ) : (
                        <div className="data-table-container">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>الاسم</th>
                                        <th>الاسم بالعربي</th>
                                        <th style={{ textAlign: 'center' }}>النسبة %</th>
                                        <th style={{ textAlign: 'center' }}>الفئة</th>
                                        <th style={{ textAlign: 'center' }}>الحالة</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {rates.map((rate) => (
                                        <tr key={rate.id}>
                                            <td className="font-medium">{rate.name}</td>
                                            <td>{rate.name_ar}</td>
                                            <td style={{ textAlign: 'center' }} className="font-mono">
                                                {formatNumber(rate.rate, 2)}%
                                            </td>
                                            <td style={{ textAlign: 'center' }}>
                                                <span className="badge badge-info">
                                                    {categoryLabels[rate.category] || rate.category}
                                                </span>
                                            </td>
                                            <td style={{ textAlign: 'center' }}>
                                                <span className={`badge ${rate.is_active ? 'badge-success' : 'badge-secondary'}`}>
                                                    {rate.is_active ? 'نشط' : 'غير نشط'}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}

            {/* ===== Transactions Tab ===== */}
            {activeTab === 'transactions' && (
                <>
                    {/* WHT Calculator */}
                    <div className="section-card" style={{ marginBottom: '24px' }}>
                        <h3 className="section-title">حاسبة ضريبة الاستقطاع</h3>
                        <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
                            <div className="form-group" style={{ flex: 1, minWidth: '200px', marginBottom: 0 }}>
                                <label className="form-label">نسبة الاستقطاع</label>
                                <select
                                    className="form-input"
                                    value={calcRateId}
                                    onChange={(e) => setCalcRateId(e.target.value)}
                                >
                                    <option value="">-- اختر النسبة --</option>
                                    {rates.map((r) => (
                                        <option key={r.id} value={r.id}>
                                            {r.name_ar || r.name} ({formatNumber(r.rate, 2)}%)
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div className="form-group" style={{ flex: 1, minWidth: '200px', marginBottom: 0 }}>
                                <label className="form-label">المبلغ الإجمالي</label>
                                <input
                                    type="number"
                                    className="form-input"
                                    placeholder="0.00"
                                    value={calcGross}
                                    onChange={(e) => setCalcGross(e.target.value)}
                                    min="0"
                                    step="0.01"
                                />
                            </div>
                            <button
                                className="btn btn-primary"
                                onClick={handleCalculate}
                                disabled={calcLoading || !calcRateId || !calcGross}
                                style={{ height: '42px' }}
                            >
                                {calcLoading ? 'جاري الحساب...' : 'احسب'}
                            </button>
                        </div>

                        {calcResult && (
                            <div style={{
                                marginTop: '20px',
                                padding: '16px',
                                background: 'rgba(37, 99, 235, 0.05)',
                                borderRadius: '12px',
                                border: '1px solid rgba(37, 99, 235, 0.15)',
                                display: 'flex',
                                gap: '32px',
                                alignItems: 'center',
                                flexWrap: 'wrap',
                            }}>
                                <div>
                                    <span className="text-secondary" style={{ fontSize: '13px' }}>مبلغ الاستقطاع</span>
                                    <div className="font-bold text-danger" style={{ fontSize: '1.25rem' }}>
                                        {formatNumber(calcResult.wht_amount)} <small>{currency}</small>
                                    </div>
                                </div>
                                <div>
                                    <span className="text-secondary" style={{ fontSize: '13px' }}>المبلغ الصافي</span>
                                    <div className="font-bold text-success" style={{ fontSize: '1.25rem' }}>
                                        {formatNumber(calcResult.net_amount)} <small>{currency}</small>
                                    </div>
                                </div>
                                <button
                                    className="btn btn-success"
                                    onClick={handleCreateTransaction}
                                    disabled={txSubmitting}
                                    style={{ marginRight: 'auto' }}
                                >
                                    {txSubmitting ? 'جاري الحفظ...' : 'إنشاء معاملة'}
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Transactions Table */}
                    <div className="section-card">
                        {txLoading ? (
                            <div className="page-center"><span className="loading"></span></div>
                        ) : transactions.length === 0 ? (
                            <div className="empty-state">
                                <p>لا توجد معاملات استقطاع بعد</p>
                            </div>
                        ) : (
                            <div className="data-table-container">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>رقم الفاتورة</th>
                                            <th>المورد</th>
                                            <th style={{ textAlign: 'left' }}>المبلغ الإجمالي</th>
                                            <th style={{ textAlign: 'center' }}>نسبة الاستقطاع</th>
                                            <th style={{ textAlign: 'left' }}>مبلغ الاستقطاع</th>
                                            <th style={{ textAlign: 'left' }}>المبلغ الصافي</th>
                                            <th>رقم الشهادة</th>
                                            <th>التاريخ</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {transactions.map((tx) => (
                                            <tr key={tx.id}>
                                                <td className="font-medium">{tx.invoice_id || '—'}</td>
                                                <td>{tx.supplier_id || '—'}</td>
                                                <td style={{ textAlign: 'left' }} className="font-mono">
                                                    {formatNumber(tx.gross_amount)} <small>{currency}</small>
                                                </td>
                                                <td style={{ textAlign: 'center' }} className="font-mono">
                                                    {formatNumber(tx.wht_rate, 2)}%
                                                </td>
                                                <td style={{ textAlign: 'left' }} className="font-mono text-danger">
                                                    {formatNumber(tx.wht_amount)} <small>{currency}</small>
                                                </td>
                                                <td style={{ textAlign: 'left' }} className="font-mono text-success">
                                                    {formatNumber(tx.net_amount)} <small>{currency}</small>
                                                </td>
                                                <td>{tx.certificate_number || '—'}</td>
                                                <td className="text-muted">{formatDate(tx.created_at)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </>
            )}

            {/* ===== Create Rate Modal ===== */}
            {showRateModal && (
                <div className="modal-overlay" onClick={() => setShowRateModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '500px' }}>
                        <div className="modal-header">
                            <h3>إضافة نسبة استقطاع</h3>
                            <button className="modal-close" onClick={() => setShowRateModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleCreateRate}>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label className="form-label">الاسم (إنجليزي)</label>
                                    <input
                                        type="text"
                                        className="form-input"
                                        value={rateForm.name}
                                        onChange={(e) => setRateForm({ ...rateForm, name: e.target.value })}
                                        required
                                        placeholder="e.g. Services WHT"
                                    />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">الاسم بالعربي</label>
                                    <input
                                        type="text"
                                        className="form-input"
                                        value={rateForm.name_ar}
                                        onChange={(e) => setRateForm({ ...rateForm, name_ar: e.target.value })}
                                        required
                                        placeholder="مثال: استقطاع خدمات"
                                    />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">النسبة (%)</label>
                                    <input
                                        type="number"
                                        className="form-input"
                                        value={rateForm.rate}
                                        onChange={(e) => setRateForm({ ...rateForm, rate: e.target.value })}
                                        required
                                        min="0"
                                        max="100"
                                        step="0.01"
                                        placeholder="5"
                                    />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">الفئة</label>
                                    <select
                                        className="form-input"
                                        value={rateForm.category}
                                        onChange={(e) => setRateForm({ ...rateForm, category: e.target.value })}
                                    >
                                        <option value="services">خدمات</option>
                                        <option value="rent">إيجار</option>
                                        <option value="royalties">إتاوات</option>
                                        <option value="consulting">استشارات</option>
                                        <option value="other">أخرى</option>
                                    </select>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setShowRateModal(false)}>
                                    إلغاء
                                </button>
                                <button type="submit" className="btn btn-primary" disabled={rateSubmitting}>
                                    {rateSubmitting ? 'جاري الحفظ...' : 'حفظ'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    )
}
