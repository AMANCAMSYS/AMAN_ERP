import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { accountingAPI } from '../../utils/api'
import { useToast } from '../../context/ToastContext'

import DateInput from '../../components/common/DateInput';
import { formatDate, formatDateTime } from '../../utils/dateUtils';
export default function OpeningBalances() {
    const { t, i18n } = useTranslation()
    const { showToast } = useToast()

    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [accounts, setAccounts] = useState([])
    const [entryInfo, setEntryInfo] = useState(null)
    const [entryDate, setEntryDate] = useState(new Date().toISOString().slice(0, 10))
    const [searchTerm, setSearchTerm] = useState('')
    const [filterType, setFilterType] = useState('')

    useEffect(() => { fetchData() }, [])

    const fetchData = async () => {
        setLoading(true)
        try {
            const res = await accountingAPI.getOpeningBalances()
            setAccounts(res.data.accounts.map(a => ({
                ...a,
                debit: a.opening_debit || 0,
                credit: a.opening_credit || 0,
            })))
            setEntryInfo(res.data.entry)
            if (res.data.entry?.entry_date) {
                setEntryDate(res.data.entry.entry_date.slice(0, 10))
            }
        } catch {
            showToast(t('opening.error_loading'), 'error')
        } finally {
            setLoading(false)
        }
    }

    const updateAccount = (id, field, value) => {
        setAccounts(prev => prev.map(a =>
            a.id === id ? { ...a, [field]: parseFloat(value) || 0 } : a
        ))
    }

    const handleSave = async () => {
        setSaving(true)
        try {
            const lines = accounts
                .filter(a => a.debit > 0 || a.credit > 0)
                .map(a => ({
                    account_id: a.id,
                    debit: a.debit,
                    credit: a.credit,
                    description: `رصيد افتتاحي - ${a.name}`,
                }))

            const res = await accountingAPI.saveOpeningBalances({ lines, date: entryDate })
            showToast(res.data.message || (t('opening.saved')), 'success')
            fetchData()
        } catch (err) {
            showToast(err.response?.data?.detail || t('common.error'), 'error')
        } finally {
            setSaving(false)
        }
    }

    const totalDebit = accounts.reduce((s, a) => s + (a.debit || 0), 0)
    const totalCredit = accounts.reduce((s, a) => s + (a.credit || 0), 0)
    const difference = totalDebit - totalCredit
    const isBalanced = Math.abs(difference) < 0.01

    const filteredAccounts = accounts.filter(a => {
        if (filterType && a.account_type !== filterType) return false
        if (searchTerm) {
            const q = searchTerm.toLowerCase()
            return (a.account_number || '').includes(q) ||
                   (a.name || '').toLowerCase().includes(q) ||
                   (a.name_en || '').toLowerCase().includes(q)
        }
        return true
    })

    const formatNum = (n) => n ? parseFloat(n).toLocaleString('en', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '-'

    const TYPE_LABELS = {
        asset: { label: t('comparison.type_asset'), color: 'primary' },
        liability: { label: t('comparison.type_liability'), color: 'warning' },
        equity: { label: t('comparison.type_equity'), color: 'success' },
        revenue: { label: t('comparison.type_revenue'), color: 'info' },
        expense: { label: t('comparison.type_expense'), color: 'danger' },
    }

    return (
        <div className="module-container" dir={i18n.dir()}>
            <div className="module-header">
                <div className="d-flex justify-content-between align-items-center flex-wrap gap-2">
                    <div>
                        <h2>📋 {t('opening.title')}</h2>
                        {entryInfo && (
                            <small className="text-muted">
                                {t('opening.entry_number')}{entryInfo.entry_number} — {formatDate(entryInfo.entry_date)}
                            </small>
                        )}
                    </div>
                    <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                        {saving ? '⏳' : '💾'} {t('opening.save')}
                    </button>
                </div>
            </div>

            {/* Summary Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '16px' }}>
                <div className="card p-3 text-center">
                    <div className="small text-muted">{t('opening.entry_date')}</div>
                    <DateInput className="form-input form-input-sm mt-1"
                        value={entryDate} onChange={e => setEntryDate(e.target.value)} />
                </div>
                <div className="card p-3 text-center">
                    <div className="small text-muted">{t('opening.total_debit')}</div>
                    <div className="fw-bold text-primary">{formatNum(totalDebit)}</div>
                </div>
                <div className="card p-3 text-center">
                    <div className="small text-muted">{t('opening.total_credit')}</div>
                    <div className="fw-bold text-success">{formatNum(totalCredit)}</div>
                </div>
                <div className={`card p-3 text-center ${!isBalanced ? 'border-danger' : 'border-success'}`}>
                    <div className="small text-muted">{t('opening.difference')}</div>
                    <div className={`fw-bold ${isBalanced ? 'text-success' : 'text-danger'}`}>
                        {isBalanced ? '✅ 0.00' : formatNum(Math.abs(difference))}
                    </div>
                </div>
            </div>

            {!isBalanced && (
                <div className="alert alert-info py-2 small">
                    ℹ️ {t('opening.auto_equity')}
                </div>
            )}

            {/* Filters */}
            <div className="row g-2 mb-3">
                <div className="col-md-6">
                    <input className="form-input form-input-sm" placeholder={t('opening.search')}
                        value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
                </div>
                <div className="col-md-3">
                    <select className="form-input" value={filterType} onChange={e => setFilterType(e.target.value)}>
                        <option value="">{t('opening.all_types')}</option>
                        {Object.entries(TYPE_LABELS).map(([k, v]) => (
                            <option key={k} value={k}>{v.label}</option>
                        ))}
                    </select>
                </div>
                <div className="col-md-3 text-end">
                    <span className="badge bg-secondary">
                        {filteredAccounts.filter(a => a.debit > 0 || a.credit > 0).length} / {filteredAccounts.length} {t('opening.accounts')}
                    </span>
                </div>
            </div>

            {loading ? (
                <div className="text-center p-5"><div className="spinner-border" /></div>
            ) : (
                <div className="data-table-container">
                    <table className="data-table table-hover">
                        <thead className="table-light">
                            <tr>
                                <th style={{ width: '10%' }}>{t('opening.account_code')}</th>
                                <th style={{ width: '35%' }}>{t('opening.account_name')}</th>
                                <th style={{ width: '12%' }}>{t('opening.type')}</th>
                                <th style={{ width: '20%' }}>{t('opening.debit')}</th>
                                <th style={{ width: '20%' }}>{t('opening.credit')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredAccounts.map(a => {
                                const tl = TYPE_LABELS[a.account_type] || {}
                                return (
                                    <tr key={a.id} className={(a.debit > 0 || a.credit > 0) ? 'table-light' : ''}>
                                        <td className="text-muted small">{a.account_number}</td>
                                        <td>{i18n.language === 'ar' ? a.name : (a.name_en || a.name)}</td>
                                        <td><span className={`badge bg-${tl.color || 'secondary'}`}>{tl.label || a.account_type}</span></td>
                                        <td>
                                            <input type="number" className="form-input form-input-sm"
                                                step="0.01" min="0" value={a.debit || ''}
                                                placeholder="0.00"
                                                onChange={e => updateAccount(a.id, 'debit', e.target.value)} />
                                        </td>
                                        <td>
                                            <input type="number" className="form-input form-input-sm"
                                                step="0.01" min="0" value={a.credit || ''}
                                                placeholder="0.00"
                                                onChange={e => updateAccount(a.id, 'credit', e.target.value)} />
                                        </td>
                                    </tr>
                                )
                            })}
                        </tbody>
                        <tfoot className="table-dark">
                            <tr className="fw-bold">
                                <td colSpan="3" className="text-end">{t('opening.total')}</td>
                                <td>{formatNum(totalDebit)}</td>
                                <td>{formatNum(totalCredit)}</td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
            )}
        </div>
    )
}
