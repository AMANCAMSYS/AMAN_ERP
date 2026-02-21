import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { treasuryAPI } from '../../utils/api'
import { useTranslation } from 'react-i18next'
import { toastEmitter } from '../../utils/toastEmitter'
import { useBranch } from '../../context/BranchContext'
import { getCurrency } from '../../utils/auth'
import { formatNumber } from '../../utils/format'
import CustomDatePicker from '../../components/common/CustomDatePicker'

function TransferForm() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { currentBranch } = useBranch()
    const currency = getCurrency() || ''

    const [loading, setLoading] = useState(false)
    const [accounts, setAccounts] = useState([])
    const [error, setError] = useState(null)

    const [form, setForm] = useState({
        transaction_date: new Date().toISOString().split('T')[0],
        amount: '',
        treasury_id: '',
        target_treasury_id: '',
        notes: '',
        reference_number: ''
    })

    useEffect(() => {
        const fetchAccounts = async () => {
            try {
                const branchId = currentBranch?.id || null
                const res = await treasuryAPI.listAccounts(branchId)
                setAccounts(res.data)
            } catch (err) {
                console.error("Failed to fetch accounts", err)
            }
        }
        fetchAccounts()
    }, [currentBranch])

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError(null)
        try {
            await treasuryAPI.createTransfer({
                ...form,
                amount: Number(form.amount),
                treasury_id: Number(form.treasury_id),
                target_treasury_id: Number(form.target_treasury_id),
                transaction_type: 'transfer',
                branch_id: currentBranch?.id || null,
                description: form.notes || form.reference_number || 'Transfer'
            })
            toastEmitter.emit(t('treasury.success_create_transfer'), 'success')
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
                <h1 className="workspace-title">{t('treasury.menu.transfer')}</h1>
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
                            <label className="form-label">{t('common.amount')} *</label>
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
                            <label className="form-label">{t('treasury.transfer_from')} *</label>
                            <select
                                required
                                className="form-input"
                                value={form.treasury_id}
                                onChange={e => setForm({ ...form, treasury_id: e.target.value })}
                            >
                                <option value="">{t('common.select')}</option>
                                {accounts.map(a => (
                                    <option key={a.id} value={a.id}>
                                        {a.name}
                                    </option>
                                ))}
                            </select>
                            {form.treasury_id && (
                                <div className="mt-2 text-sm">
                                    <span className="text-secondary">{t('treasury.available_balance')}: </span>
                                    <span className="fw-bold text-success">
                                        {formatNumber(accounts.find(a => a.id.toString() === form.treasury_id.toString())?.current_balance)} {currency}
                                    </span>
                                </div>
                            )}
                        </div>
                        <div className="form-group" style={{ flex: 1 }}>
                            <label className="form-label">{t('treasury.transfer_to')} *</label>
                            <select
                                required
                                className="form-input"
                                value={form.target_treasury_id}
                                onChange={e => setForm({ ...form, target_treasury_id: e.target.value })}
                            >
                                <option value="">{t('common.select')}</option>
                                {accounts.filter(a => a.id.toString() !== form.treasury_id).map(a => (
                                    <option key={a.id} value={a.id}>
                                        {a.name}
                                    </option>
                                ))}
                            </select>
                            {form.target_treasury_id && (
                                <div className="mt-2 text-sm">
                                    <span className="text-secondary">{t('treasury.available_balance')}: </span>
                                    <span className="fw-bold text-success">
                                        {formatNumber(accounts.find(a => a.id.toString() === form.target_treasury_id.toString())?.current_balance)} {currency}
                                    </span>
                                </div>
                            )}
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

export default TransferForm
