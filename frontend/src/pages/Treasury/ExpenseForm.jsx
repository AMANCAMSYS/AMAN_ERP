import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { treasuryAPI, accountingAPI } from '../../utils/api'
import { useTranslation } from 'react-i18next'
import { toastEmitter } from '../../utils/toastEmitter'
import { useBranch } from '../../context/BranchContext'
import { getCurrency } from '../../utils/auth'
import { formatNumber } from '../../utils/format'
import CustomDatePicker from '../../components/common/CustomDatePicker'
import BackButton from '../../components/common/BackButton';

function ExpenseForm() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { currentBranch, branches } = useBranch()
    const currency = getCurrency() || ''

    const [loading, setLoading] = useState(false)
    const [accounts, setAccounts] = useState([])
    const [glAccounts, setGlAccounts] = useState([])
    const [error, setError] = useState(null)

    const [form, setForm] = useState({
        transaction_date: new Date().toISOString().split('T')[0],
        amount: '',
        treasury_id: '',
        target_account_id: '',
        notes: '',
        reference_number: '',
        branch_id: ''
    })

    useEffect(() => {
        const fetchData = async () => {
            try {
                const branchId = currentBranch?.id || null
                const gas = await accountingAPI.list()
                setGlAccounts(gas.data.filter(a => a.account_type === 'expense'))
                // Set default branch if not set
                if (!form.branch_id && currentBranch) {
                    setForm(prev => ({ ...prev, branch_id: currentBranch.id.toString() }))
                }
            } catch (err) {
                console.error("Failed to load global data", err)
            }
        }
        fetchData()
    }, [currentBranch])

    useEffect(() => {
        const fetchTreasuryAccounts = async () => {
            if (!form.branch_id) {
                setAccounts([])
                return
            }
            try {
                const accs = await treasuryAPI.listAccounts(Number(form.branch_id))
                setAccounts(accs.data)
                // Reset treasury selection if current selection is not in the new list
                if (form.treasury_id && !accs.data.some(a => a.id.toString() === form.treasury_id.toString())) {
                    setForm(prev => ({ ...prev, treasury_id: '' }))
                }
            } catch (err) {
                console.error("Failed to load treasury accounts", err)
            }
        }
        fetchTreasuryAccounts()
    }, [form.branch_id])

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError(null)
        try {
            await treasuryAPI.createExpense({
                ...form,
                amount: Number(form.amount),
                treasury_id: Number(form.treasury_id),
                target_account_id: Number(form.target_account_id),
                transaction_type: 'expense',
                branch_id: form.branch_id ? Number(form.branch_id) : null,
                description: form.notes || form.reference_number || 'Expense'
            })
            toastEmitter.emit(t('treasury.success_create_expense'), 'success')
            navigate('/treasury')
        } catch (err) {
            const errorData = err.response?.data?.detail
            if (Array.isArray(errorData)) {
                setError(errorData.map(e => `${e.loc.join('.')}: ${e.msg}`).join(', '))
            } else if (typeof errorData === 'object') {
                setError(JSON.stringify(errorData))
            } else {
                setError(errorData || t('common.error_occurred'))
            }
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <h1 className="workspace-title">{t('treasury.menu.expense')}</h1>
                <p className="workspace-subtitle">{t('treasury.subtitle')}</p>
            </div>

            {error && <div className="alert alert-danger mb-4">{error}</div>}

            <form onSubmit={handleSubmit}>
                <div className="card mb-4 p-4">
                    <h3 className="section-title">{t('common.details')}</h3>
                    <div className="form-row">
                        <div className="form-group" style={{ flex: 1 }}>
                            <CustomDatePicker
                                label={t('common.date')}
                                selected={form.transaction_date}
                                onChange={dateStr => setForm({ ...form, transaction_date: dateStr })}
                                required
                            />
                        </div>
                        <div className="form-group" style={{ flex: 1 }}>
                            <label className="form-label">{t('treasury.expense_amount')} *</label>
                            <div className="input-group">
                                <span className="input-group-text">
                                    {currency}
                                </span>
                                <input
                                    type="number"
                                    required
                                    className="form-input"
                                    placeholder="0.00"
                                    value={form.amount}
                                    onChange={e => setForm({ ...form, amount: e.target.value })}
                                />
                            </div>
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group" style={{ flex: 1 }}>
                            <label className="form-label">{t('treasury.allocation_branch')} *</label>
                            <select
                                className="form-input"
                                required
                                value={form.branch_id}
                                onChange={e => setForm({ ...form, branch_id: e.target.value })}
                            >
                                <option value="">{t('common.select')}</option>
                                {branches.map(b => (
                                    <option key={b.id} value={b.id}>
                                        {b.branch_name}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div className="form-group" style={{ flex: 1 }}>
                            <label className="form-label">{t('treasury.account_label')} *</label>
                            <select
                                className="form-input"
                                required
                                value={form.treasury_id}
                                onChange={e => setForm({ ...form, treasury_id: e.target.value })}
                            >
                                <option value="">{t('common.select')}</option>
                                {accounts.map(acc => (
                                    <option key={acc.id} value={acc.id}>
                                        {acc.name}
                                    </option>
                                ))}
                            </select>
                            {form.treasury_id && (
                                <div className="mt-2 text-sm">
                                    <span className="text-secondary">{t('treasury.available_balance')}: </span>
                                    <span className={`fw-bold ${accounts.find(a => a.id.toString() === form.treasury_id.toString())?.current_balance < 0 ? 'text-danger' : 'text-success'}`}>
                                        {formatNumber(accounts.find(a => a.id.toString() === form.treasury_id.toString())?.current_balance)} {currency}
                                    </span>
                                </div>
                            )}
                        </div>
                        <div className="form-group" style={{ flex: 1 }}>
                            <label className="form-label">{t('treasury.expense_type')} *</label>
                            <select
                                className="form-input"
                                required
                                value={form.target_account_id}
                                onChange={e => setForm({ ...form, target_account_id: e.target.value })}
                            >
                                <option value="">{t('common.select')}</option>
                                {glAccounts
                                    .filter(acc => !acc.branch_id || acc.branch_id.toString() === form.branch_id.toString())
                                    .map(acc => {
                                        return (
                                            <option key={acc.id} value={acc.id}>
                                                {acc.account_code} - {acc.name}
                                            </option>
                                        );
                                    })
                                }
                            </select>
                        </div>
                    </div>

                    <div className="form-group mt-3">
                        <label className="form-label">{t('common.reference')}</label>
                        <input
                            type="text"
                            className="form-input"
                            placeholder={t('common.reference_placeholder')}
                            value={form.reference_number}
                            onChange={e => setForm({ ...form, reference_number: e.target.value })}
                        />
                    </div>

                    <div className="form-group mt-3">
                        <label className="form-label">{t('common.notes')}</label>
                        <textarea
                            className="form-input"
                            rows="3"
                            value={form.notes}
                            onChange={e => setForm({ ...form, notes: e.target.value })}
                        ></textarea>
                    </div>

                    <div style={{ display: 'flex', gap: '12px', marginTop: '24px', justifyContent: 'flex-end' }}>
                        <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={() => navigate('/treasury')}
                        >
                            {t('common.cancel')}
                        </button>
                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={loading}
                        >
                            {loading ? t('common.saving') : t('common.save')}
                        </button>
                    </div>
                </div>
            </form>
        </div>
    )
}

export default ExpenseForm
