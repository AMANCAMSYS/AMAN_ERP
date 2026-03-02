import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { landedCostsAPI } from '../../utils/api'
import { getCurrency } from '../../utils/auth'
import { useTranslation } from 'react-i18next'
import { formatShortDate } from '../../utils/dateUtils'
import { useToast } from '../../context/ToastContext'
import BackButton from '../../components/common/BackButton'

function LandedCosts() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { showToast } = useToast()
    const currency = getCurrency()
    const [costs, setCosts] = useState([])
    const [loading, setLoading] = useState(true)
    const [showForm, setShowForm] = useState(false)
    const [form, setForm] = useState({ reference_type: 'purchase_order', reference_id: '', description: '', items: [] })
    const [newItem, setNewItem] = useState({ cost_type: 'freight', description: '', amount: '' })

    useEffect(() => {
        landedCostsAPI.list().then(r => setCosts(r.data)).catch(console.error).finally(() => setLoading(false))
    }, [])

    const addItem = () => {
        if (!newItem.amount) return
        setForm(f => ({ ...f, items: [...f.items, { ...newItem, amount: Number(newItem.amount) }] }))
        setNewItem({ cost_type: 'freight', description: '', amount: '' })
    }

    const handleCreate = async () => {
        try {
            const res = await landedCostsAPI.create(form)
            showToast(t('landed_costs.created'), 'success')
            navigate(`/buying/landed-costs/${res.data.id}`)
        } catch (err) {
            showToast(err.response?.data?.detail || t('common.error'), 'error')
        }
    }

    if (loading) return <div className="p-4"><span className="loading"></span></div>

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">📦 {t('landed_costs.title')}</h1>
                    <p className="workspace-subtitle">{t('landed_costs.subtitle')}</p>
                </div>
                <div className="header-actions">
                    <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
                        + {t('landed_costs.create_new')}
                    </button>
                </div>
            </div>

            {showForm && (
                <div className="card p-4 mb-4">
                    <h3 className="card-title mb-3">{t('landed_costs.create_new')}</h3>
                    <div className="form-grid-3">
                        <div className="form-group">
                            <label>{t('landed_costs.reference_type')}</label>
                            <select className="form-select" value={form.reference_type} onChange={e => setForm(f => ({ ...f, reference_type: e.target.value }))}>
                                <option value="purchase_order">{t('landed_costs.purchase_order')}</option>
                                <option value="grn">{t('landed_costs.grn')}</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label>{t('landed_costs.reference_id')}</label>
                            <input type="number" className="form-input" value={form.reference_id} onChange={e => setForm(f => ({ ...f, reference_id: e.target.value }))} />
                        </div>
                        <div className="form-group">
                            <label>{t('common.description')}</label>
                            <input type="text" className="form-input" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
                        </div>
                    </div>

                    <h4 className="mt-3 mb-2">{t('landed_costs.cost_items')}</h4>
                    <div className="form-grid-4">
                        <select className="form-select" value={newItem.cost_type} onChange={e => setNewItem(n => ({ ...n, cost_type: e.target.value }))}>
                            <option value="freight">{t('landed_costs.freight')}</option>
                            <option value="customs">{t('landed_costs.customs')}</option>
                            <option value="insurance">{t('landed_costs.insurance')}</option>
                            <option value="other">{t('common.other')}</option>
                        </select>
                        <input type="text" className="form-input" placeholder={t('common.description')} value={newItem.description} onChange={e => setNewItem(n => ({ ...n, description: e.target.value }))} />
                        <input type="number" className="form-input" step="0.01" placeholder={t('common.amount')} value={newItem.amount} onChange={e => setNewItem(n => ({ ...n, amount: e.target.value }))} />
                        <button type="button" className="btn btn-secondary" onClick={addItem}>+</button>
                    </div>

                    {form.items.length > 0 && (
                        <table className="data-table mt-2">
                            <thead><tr><th>{t('common.type')}</th><th>{t('common.description')}</th><th>{t('common.amount')}</th><th></th></tr></thead>
                            <tbody>
                                {form.items.map((item, i) => (
                                    <tr key={i}>
                                        <td>{t(`landed_costs.${item.cost_type}`, item.cost_type)}</td>
                                        <td>{item.description}</td>
                                        <td>{Number(item.amount).toLocaleString()} {currency}</td>
                                        <td><button className="btn-icon text-danger" onClick={() => setForm(f => ({ ...f, items: f.items.filter((_, j) => j !== i) }))}>🗑️</button></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}

                    <div className="mt-3 flex gap-2">
                        <button className="btn btn-primary" onClick={handleCreate} disabled={form.items.length === 0}>
                            {t('common.save')}
                        </button>
                        <button className="btn btn-secondary" onClick={() => setShowForm(false)}>{t('common.cancel')}</button>
                    </div>
                </div>
            )}

            <div className="card">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>{t('landed_costs.lc_number')}</th>
                            <th>{t('common.date')}</th>
                            <th>{t('landed_costs.total_cost')}</th>
                            <th>{t('common.status')}</th>
                            <th>{t('common.actions')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {costs.length === 0 ? (
                            <tr><td colSpan="5" className="text-center py-5 text-muted">{t('landed_costs.empty')}</td></tr>
                        ) : costs.map(c => (
                            <tr key={c.id}>
                                <td className="font-medium text-primary">{c.lc_number}</td>
                                <td>{formatShortDate(c.created_at)}</td>
                                <td className="font-bold">{Number(c.total_cost).toLocaleString()} <small>{currency}</small></td>
                                <td><span className={`status-badge ${c.status}`}>{c.status}</span></td>
                                <td><button onClick={() => navigate(`/buying/landed-costs/${c.id}`)} className="btn-icon">👁️</button></td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}

export default LandedCosts
