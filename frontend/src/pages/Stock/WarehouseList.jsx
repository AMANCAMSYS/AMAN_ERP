import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { inventoryAPI, branchesAPI } from '../../utils/api'
import { Edit2, Trash2, Plus, X, Warehouse } from 'lucide-react'
import { useBranch } from '../../context/BranchContext'
import { useToast } from '../../context/ToastContext'
import BackButton from '../../components/common/BackButton'
import DataTable from '../../components/common/DataTable'
import SearchFilter from '../../components/common/SearchFilter'

function WarehouseList() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { currentBranch } = useBranch()
    const { showToast } = useToast()
    const [warehouses, setWarehouses] = useState([])
    const [branches, setBranches] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [showModal, setShowModal] = useState(false)
    const [editingItem, setEditingItem] = useState(null)
    const [formData, setFormData] = useState({ name: '', code: '', branch_id: null })
    const [search, setSearch] = useState('')

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
            showToast(t('stock.warehouses.validation.error_fetch'), 'error')
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
            showToast(t('stock.warehouses.validation.success_save'), 'success')
            setShowModal(false)
            setEditingItem(null)
            setFormData({ name: '', code: '', branch_id: null })
            fetchWarehouses()
        } catch (err) {
            showToast(t('stock.warehouses.validation.error_save'), 'error')
        }
    }

    const handleDelete = async (id) => {
        if (window.confirm(t('stock.warehouses.validation.delete_confirm'))) {
            try {
                await inventoryAPI.deleteWarehouse(id)
                fetchWarehouses()
            } catch (err) {
                showToast(t('stock.warehouses.validation.delete_error'), 'error')
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

    const filteredWarehouses = useMemo(() => {
        if (!search) return warehouses
        const q = search.toLowerCase()
        return warehouses.filter(wh =>
            (wh.name || '').toLowerCase().includes(q) ||
            (wh.code || '').toLowerCase().includes(q) ||
            (wh.branch_name || '').toLowerCase().includes(q)
        )
    }, [warehouses, search])

    const columns = [
        {
            key: 'code',
            label: t('stock.warehouses.table.code'),
            render: (val) => <span className="font-medium text-primary">{val}</span>,
        },
        {
            key: 'name',
            label: t('stock.warehouses.table.name'),
            render: (val) => <span style={{ fontWeight: 600 }}>{val}</span>,
        },
        {
            key: 'branch_name',
            label: t('branches.name'),
            render: (val) => <span className="text-muted">{val || '-'}</span>,
        },
        {
            key: '_actions',
            label: t('stock.warehouses.table.actions'),
            width: '100px',
            render: (_, row) => (
                <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                        onClick={(e) => {
                            e.stopPropagation()
                            openModal(row)
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
                            handleDelete(row.id)
                        }}
                        className="btn-icon"
                        style={{ width: '30px', height: '30px', background: '#fee2e2', color: '#ef4444' }}
                        title={t('common.delete')}
                    >
                        <Trash2 size={14} />
                    </button>
                </div>
            ),
        },
    ]

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
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

            <SearchFilter
                value={search}
                onChange={setSearch}
                placeholder={t('stock.warehouses.search_placeholder', 'بحث بالاسم أو الكود...')}
            />

            <DataTable
                columns={columns}
                data={filteredWarehouses}
                loading={loading}
                onRowClick={(row) => navigate(`/stock/warehouses/${row.id}`)}
                emptyIcon="🏭"
                emptyTitle={t('stock.warehouses.empty')}
            />

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
