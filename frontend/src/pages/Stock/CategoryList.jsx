import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { inventoryAPI } from '../../utils/api'
import { Edit2, Trash2, Plus, X, Search, Layers } from 'lucide-react'
import { useBranch } from '../../context/BranchContext'
import { toastEmitter } from '../../utils/toastEmitter'
import BackButton from '../../components/common/BackButton';

function CategoryList() {
    const { t } = useTranslation()
    const { currentBranch } = useBranch()
    const [categories, setCategories] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [showModal, setShowModal] = useState(false)
    const [editingItem, setEditingItem] = useState(null)
    const [formData, setFormData] = useState({ name: '', code: '' })

    const fetchCategories = useCallback(async () => {
        try {
            setLoading(true)
            const res = await inventoryAPI.listCategories({ branch_id: currentBranch?.id })
            setCategories(res.data)
        } catch (err) {
            setError(t('stock.categories.validation.error_fetch'))
        } finally {
            setLoading(false)
        }
    }, [currentBranch, t])

    useEffect(() => {
        fetchCategories()
    }, [fetchCategories])

    const handleSubmit = async (e) => {
        e.preventDefault()
        try {
            if (editingItem) {
                // Update: Do not send branch_id to keep it global or as is. 
                // Using { ...formData } without branch_id
                await inventoryAPI.updateCategory(editingItem.id, { ...formData })
            } else {
                // Create: Do not send branch_id to make it global
                await inventoryAPI.createCategory({ ...formData })
            }
            setShowModal(false)
            setEditingItem(null)
            setFormData({ name: '', code: '' })
            fetchCategories()
        } catch (err) {
            toastEmitter.emit(t('stock.categories.validation.error_save'), 'error')
        }
    }

    const handleDelete = async (id) => {
        if (window.confirm(t('stock.categories.validation.delete_confirm'))) {
            try {
                await inventoryAPI.deleteCategory(id)
                fetchCategories()
            } catch (err) {
                toastEmitter.emit(t('stock.categories.validation.delete_error'), 'error')
            }
        }
    }

    const openModal = async (item = null) => {
        if (item) {
            setEditingItem(item)
            setFormData({ name: item.name, code: item.code })
            setShowModal(true)
        } else {
            setEditingItem(null)
            setFormData({ name: '', code: '...' })
            setShowModal(true)
            try {
                const res = await inventoryAPI.getNextCategoryCode()
                setFormData(prev => ({ ...prev, code: res.data.next_code }))
            } catch (err) {
                console.error("Failed to fetch next code", err)
                // Fallback or leave empty for manual input
                setFormData(prev => ({ ...prev, code: '' }))
            }
        }
    }

    if (loading) return <div className="page-center"><span className="loading"></span></div>

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div>
                    <h1 className="workspace-title" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <Layers size={28} className="text-primary" />
                        {t('stock.categories.title')}
                    </h1>
                    <p className="workspace-subtitle">{t('stock.categories.subtitle')}</p>
                </div>
                <button className="btn btn-primary" onClick={() => openModal()}>
                    <Plus size={18} />
                    {t('stock.categories.new_category')}
                </button>
            </div>

            <div className="data-table-container">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>{t('stock.categories.table.code')}</th>
                            <th>{t('stock.categories.table.name')}</th>
                            <th style={{ width: '100px' }}>{t('stock.categories.table.actions')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {categories.map(cat => (
                            <tr key={cat.id} className="hover-row">
                                <td className="font-medium text-primary">{cat.code}</td>
                                <td style={{ fontWeight: 600 }}>{cat.name}</td>
                                <td>
                                    <div style={{ display: 'flex', gap: '8px' }}>
                                        <button
                                            onClick={() => openModal(cat)}
                                            className="btn-icon"
                                            style={{ width: '30px', height: '30px', background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}
                                            title={t('common.edit')}
                                        >
                                            <Edit2 size={14} />
                                        </button>
                                        <button
                                            onClick={() => handleDelete(cat.id)}
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
                        {categories.length === 0 && (
                            <tr>
                                <td colSpan="3" className="text-center" style={{ padding: '60px' }}>
                                    <Layers size={48} style={{ color: 'var(--border)', marginBottom: '16px' }} />
                                    <p style={{ color: 'var(--text-secondary)' }}>{t('stock.categories.empty')}</p>
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
                                {editingItem ? t('stock.categories.editing_category') : t('stock.categories.new_category')}
                            </h2>
                            <button onClick={() => setShowModal(false)}><X size={20} /></button>
                        </div>

                        <form onSubmit={handleSubmit}>
                            <div className="form-group">
                                <label className="form-label">{t('stock.categories.form.name')}</label>
                                <input
                                    className="form-input"
                                    value={formData.name}
                                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                                    required
                                    autoFocus
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('stock.categories.form.code')}</label>
                                <input
                                    className="form-input"
                                    value={formData.code}
                                    onChange={e => setFormData({ ...formData, code: e.target.value })}
                                    required
                                />
                            </div>
                            <div style={{ display: 'flex', gap: '10px', marginTop: '24px' }}>
                                <button type="submit" className="btn btn-primary btn-block">{t('stock.categories.form.save')}</button>
                                <button type="button" className="btn" style={{ background: 'var(--bg-secondary)', width: '100%' }} onClick={() => setShowModal(false)}>{t('stock.categories.form.cancel')}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    )
}

export default CategoryList
