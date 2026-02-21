import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { inventoryAPI, branchesAPI } from '../../utils/api'
import { Edit2, Trash2, Plus, X, Warehouse } from 'lucide-react'
import { useBranch } from '../../context/BranchContext'
import { toastEmitter } from '../../utils/toastEmitter'

function WarehouseList() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { currentBranch } = useBranch()
    const [warehouses, setWarehouses] = useState([])
    const [branches, setBranches] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [showModal, setShowModal] = useState(false)
    const [editingItem, setEditingItem] = useState(null)
    const [formData, setFormData] = useState({ name: '', code: '', branch_id: null })

    const fetchWarehouses = async () => {
        try {
            setLoading(true)
            const res = await inventoryAPI.listWarehouses({ branch_id: currentBranch?.id })
            setWarehouses(res.data)
        } catch (err) {
            setError(t('stock.warehouses.validation.error_fetch'))
        } finally {
            setLoading(false)
        }
    }

    const fetchBranches = async () => {
        try {
            const res = await branchesAPI.list()
            setBranches(res.data)
        } catch (err) {
            console.error('Error fetching branches:', err)
        }
    }

    useEffect(() => {
        fetchWarehouses()
        fetchBranches()
    }, [currentBranch])

    const handleSubmit = async (e) => {
        e.preventDefault()
        try {
            if (editingItem) {
                await inventoryAPI.updateWarehouse(editingItem.id, formData)
            } else {
                await inventoryAPI.createWarehouse(formData)
            }
            toastEmitter.emit(t('stock.warehouses.validation.success_save'), 'success')
            setShowModal(false)
            setEditingItem(null)
            setFormData({ name: '', code: '', branch_id: null })
            fetchWarehouses()
        } catch (err) {
            toastEmitter.emit(t('stock.warehouses.validation.error_save'), 'error')
        }
    }

    const handleDelete = async (id) => {
        if (window.confirm(t('stock.warehouses.validation.delete_confirm'))) {
            try {
                await inventoryAPI.deleteWarehouse(id)
                fetchWarehouses()
            } catch (err) {
                toastEmitter.emit(t('stock.warehouses.validation.delete_error'), 'error')
            }
        }
    }

    const openModal = (item = null) => {
        if (item) {
            setEditingItem(item)
            setFormData({ name: item.name, code: item.code, branch_id: item.branch_id || null })
        } else {
            setEditingItem(null)

            // Sequential code generation
            let nextNum = 1;
            if (warehouses && warehouses.length > 0) {
                const codes = warehouses
                    .map(wh => {
                        const match = wh.code?.match(/WH-(\d+)/);
                        return match ? parseInt(match[1]) : 0;
                    })
                    .filter(n => !isNaN(n));

                if (codes.length > 0) {
                    nextNum = Math.max(...codes) + 1;
                }
            }

            const nextCode = `WH-${String(nextNum).padStart(3, '0')}`;
            setFormData({ name: '', code: nextCode, branch_id: currentBranch?.id || null })
        }
        setShowModal(true)
    }

    if (loading) return <div className="page-center"><span className="loading"></span></div>

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div>
                    <h1 className="workspace-title" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <Warehouse size={28} className="text-primary" />
                        {t('stock.warehouses.title')}
                    </h1>
                    <p className="workspace-subtitle">{t('stock.warehouses.subtitle')}</p>
                </div>
                <button className="btn btn-primary" onClick={() => openModal()}>
                    <Plus size={18} />
                    {t('stock.warehouses.new_warehouse')}
                </button>
            </div>

            <div className="data-table-container">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>{t('stock.warehouses.table.code')}</th>
                            <th>{t('stock.warehouses.table.name')}</th>
                            <th>{t('branches.name')}</th>
                            <th style={{ width: '100px' }}>{t('stock.warehouses.table.actions')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {warehouses.map(wh => (
                            <tr
                                key={wh.id}
                                className="hover-row"
                                onClick={() => navigate(`/stock/warehouses/${wh.id}`)}
                                style={{ cursor: 'pointer' }}
                            >
                                <td className="font-medium text-primary">{wh.code}</td>
                                <td style={{ fontWeight: 600 }}>{wh.name}</td>
                                <td className="text-muted">{wh.branch_name || '-'}</td>
                                <td>
                                    <div style={{ display: 'flex', gap: '8px' }}>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation()
                                                openModal(wh)
                                            }}
                                            className="btn-icon"
                                            style={{ width: '30px', height: '30px', background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}
                                            title={t('common.edit')}
                                        >
                                            <Edit2 size={14} />
                                        </button>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation()
                                                handleDelete(wh.id)
                                            }}
                                            className="btn-icon"
                                            style={{ width: '30px', height: '30px', background: '#fee2e2', color: '#ef4444' }}
                                            title={t('common.delete')}
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                        {warehouses.length === 0 && (
                            <tr>
                                <td colSpan="4" className="text-center" style={{ padding: '60px' }}>
                                    <Warehouse size={48} style={{ color: 'var(--border)', marginBottom: '16px' }} />
                                    <p style={{ color: 'var(--text-secondary)' }}>{t('stock.warehouses.empty')}</p>
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* Modal */}
            {showModal && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.5)', zIndex: 1000,
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                }}>
                    <div className="fade-in" style={{
                        background: 'white', padding: '24px', borderRadius: '12px',
                        width: '400px', maxWidth: '90%'
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
                            <h2 style={{ fontSize: '18px', fontWeight: '700' }}>
                                {editingItem ? t('stock.warehouses.form.edit_title') : t('stock.warehouses.form.title')}
                            </h2>
                            <button onClick={() => setShowModal(false)}><X size={20} /></button>
                        </div>

                        <form onSubmit={handleSubmit}>
                            <div className="form-group">
                                <label className="form-label">{t('stock.warehouses.form.name')}</label>
                                <input
                                    className="form-input"
                                    value={formData.name}
                                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                                    required
                                    autoFocus
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('stock.warehouses.form.code')}</label>
                                <input
                                    className="form-input"
                                    value={formData.code}
                                    onChange={e => setFormData({ ...formData, code: e.target.value })}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('branches.select_branch')}</label>
                                <select
                                    className="form-input"
                                    value={formData.branch_id || ''}
                                    onChange={e => setFormData({ ...formData, branch_id: e.target.value ? parseInt(e.target.value) : null })}
                                >
                                    <option value="">-- {t('common.select')} --</option>
                                    {branches.map(b => (
                                        <option key={b.id} value={b.id}>{b.branch_name}</option>
                                    ))}
                                </select>
                            </div>
                            <div style={{ display: 'flex', gap: '10px', marginTop: '24px' }}>
                                <button type="submit" className="btn btn-primary btn-block">{t('stock.warehouses.form.save')}</button>
                                <button type="button" className="btn" style={{ background: 'var(--bg-secondary)', width: '100%' }} onClick={() => setShowModal(false)}>{t('stock.warehouses.form.cancel')}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    )
}

export default WarehouseList
