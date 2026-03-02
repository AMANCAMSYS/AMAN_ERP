import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { inventoryAPI, api } from '../../utils/api'
import { getCurrency, hasPermission } from '../../utils/auth'
import { useBranch } from '../../context/BranchContext'
import { formatNumber } from '../../utils/format'
import { ChevronDown, ChevronUp, Info } from 'lucide-react'
import Pagination, { usePagination } from '../../components/common/Pagination'

import { formatShortDate, formatDateTime } from '../../utils/dateUtils';
import BackButton from '../../components/common/BackButton';
import { useToast } from '../../context/ToastContext'

function ProductList() {
    const { t } = useTranslation()
  const { showToast } = useToast()
    const navigate = useNavigate()
    const { currentBranch } = useBranch()
    const [products, setProducts] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [expandedProductId, setExpandedProductId] = useState(null)
    const [breakdownData, setBreakdownData] = useState(null)
    const [loadingBreakdown, setLoadingBreakdown] = useState(false)
    const [policyType, setPolicyType] = useState('global_wac')
    const [showDeleteModal, setShowDeleteModal] = useState(false)
    const [productToDelete, setProductToDelete] = useState(null)

    const currency = getCurrency()
    const canViewCost = hasPermission('stock.view_cost')
    const canCreate = hasPermission('stock.create_product')
    const canDelete = hasPermission('stock.delete_product')
    const { currentPage, pageSize, totalItems, paginatedItems, onPageChange, onPageSizeChange } = usePagination(products)

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true)
                const response = await inventoryAPI.listProducts({ branch_id: currentBranch?.id })
                setProducts(response.data)

                // Fetch current policy
                try {
                    const policyRes = await api.get('/costing-policies/current')
                    setPolicyType(policyRes.data.policy_type)
                } catch (e) {
                    console.warn("Could not fetch policy, defaulting to global")
                }
            } catch (err) {
                setError(t('stock.products.validation.error_fetch'))
                console.error(err)
            } finally {
                setLoading(false)
            }
        }
        fetchData()
    }, [currentBranch, t])

    const handleExpand = async (e, productId) => {
        e.stopPropagation() // Prevent row click navigation

        if (expandedProductId === productId) {
            setExpandedProductId(null)
            setBreakdownData(null)
            return
        }

        setExpandedProductId(productId)
        setLoadingBreakdown(true)
        try {
            const res = await api.get(`/inventory/products/${productId}/cost-breakdown`)
            setBreakdownData(res.data.breakdown)
        } catch (err) {
            console.error("Failed to load breakdown", err)
        } finally {
            setLoadingBreakdown(false)
        }
    }

    const handleDeleteClick = (e, product) => {
        e.stopPropagation()
        setProductToDelete(product)
        setShowDeleteModal(true)
    }

    const handleDeleteConfirm = async () => {
        try {
            await inventoryAPI.deleteProduct(productToDelete.id)
            setProducts(products.filter(p => p.id !== productToDelete.id))
            setShowDeleteModal(false)
            setProductToDelete(null)
        } catch (err) {
            const errorMsg = err.response?.data?.detail || t('stock.products.validation.error_delete')
            showToast(errorMsg, 'error')
        }
    }

    if (loading) return <div className="page-center"><span className="loading"></span></div>

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className="workspace-title">{t('stock.products.title')}</h1>
                        <p className="workspace-subtitle">{t('stock.products.subtitle')}</p>
                    </div>
                    {canCreate && (
                        <button className="btn btn-primary" onClick={() => navigate('/stock/products/new')}>
                            <span style={{ marginLeft: '8px' }}>+</span>
                            {t('stock.products.new_product')}
                        </button>
                    )}
                </div>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <div className="data-table-container">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th style={{ width: '5%' }}></th>
                            <th style={{ width: '15%' }}>{t('stock.products.table.code')}</th>
                            <th style={{ width: '25%' }}>{t('stock.products.table.name')}</th>
                            <th style={{ width: '10%' }}>{t('stock.products.table.type')}</th>
                            <th style={{ width: '15%' }}>{t('stock.products.table.category')}</th>
                            {canViewCost && <th style={{ width: '10%' }}>{t('stock.products.table.cost')}</th>}
                            <th style={{ width: '10%' }}>{t('stock.products.table.price')}</th>
                            <th style={{ width: '10%' }}>{t('stock.products.table.reserved')}</th>
                            <th style={{ width: '10%' }}>{t('stock.products.table.stock')}</th>
                            {canDelete && <th style={{ width: '80px' }}>{t('common.actions')}</th>}
                        </tr>
                    </thead>
                    <tbody>
                        {products.length === 0 ? (
                            <tr>
                                <td colSpan={canViewCost ? 10 : 9} className="start-guide">
                                    <div style={{ padding: '60px 20px', textAlign: 'center' }}>
                                        <div style={{ fontSize: '48px', marginBottom: '16px' }}>📦</div>
                                        <h3 style={{ fontSize: '18px', marginBottom: '8px' }}>{t('stock.products.empty')}</h3>
                                        {canCreate && (
                                            <button className="btn btn-primary" onClick={() => navigate('/stock/products/new')}>
                                                {t('stock.products.add_first')}
                                            </button>
                                        )}
                                    </div>
                                </td>
                            </tr>
                        ) : (
                            paginatedItems.map(product => (
                                <React.Fragment key={product.id}>
                                    <tr
                                        style={{ cursor: 'pointer', backgroundColor: expandedProductId === product.id ? 'var(--bg-secondary)' : 'inherit' }}
                                        onClick={() => navigate(`/stock/products/${product.id}`)}
                                    >
                                        <td onClick={(e) => handleExpand(e, product.id)} style={{ textAlign: 'center', cursor: 'pointer' }}>
                                            {(policyType !== 'global_wac' && canViewCost) && (
                                                expandedProductId === product.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />
                                            )}
                                        </td>
                                        <td style={{ fontFamily: 'monospace', fontWeight: 'bold', color: 'var(--text-secondary)' }}>
                                            {product.item_code}
                                        </td>
                                        <td>
                                            <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{product.item_name}</div>
                                        </td>
                                        <td>
                                            <span className={`badge ${product.item_type === 'service' ? 'badge-info' : 'badge-primary'}`}>
                                                {t(`stock.products.types.${product.item_type}`)}
                                            </span>
                                        </td>
                                        <td>{product.category_name || '-'}</td>

                                        {canViewCost && (
                                            <td>
                                                <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                                                    {formatNumber(product.buying_price || 0)} {currency}
                                                </div>
                                            </td>
                                        )}

                                        <td>
                                            <div style={{ fontWeight: '600', color: 'var(--success)' }}>
                                                {formatNumber(product.selling_price)} {currency}
                                            </div>
                                        </td>
                                        <td>
                                            <div style={{ fontWeight: '500', color: 'var(--warning)' }}>
                                                {formatNumber(product.reserved_quantity)} <span style={{ fontSize: '12px' }}>{product.unit}</span>
                                            </div>
                                        </td>
                                        <td>
                                            <div style={{ fontWeight: '500' }}>
                                                {formatNumber(product.current_stock)} <span style={{ fontSize: '12px' }}>{product.unit}</span>
                                            </div>
                                        </td>
                                        {canDelete && (
                                            <td>
                                                <button
                                                    onClick={(e) => handleDeleteClick(e, product)}
                                                    className="btn-icon"
                                                    title={t('common.delete')}
                                                    style={{ color: 'var(--danger)', padding: '4px 8px' }}
                                                >
                                                    🗑️
                                                </button>
                                            </td>
                                        )}
                                    </tr>
                                    {expandedProductId === product.id && (
                                        <tr>
                                            <td colSpan={canDelete ? (canViewCost ? 10 : 9) : (canViewCost ? 9 : 8)} style={{ padding: '0', borderBottom: '1px solid var(--border-color)' }}>
                                                <div style={{ padding: '16px', background: 'var(--bg-subtle)' }}>
                                                    <h4 style={{ fontSize: '14px', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                        <Info size={16} /> {t('stock.products.cost_by_warehouse')}
                                                    </h4>
                                                    {loadingBreakdown ? (
                                                        <div className="spinner-small"></div>
                                                    ) : (
                                                        <table className="table table-sm" style={{ background: 'white', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                                                            <thead>
                                                                <tr style={{ background: 'var(--bg-secondary)' }}>
                                                                    <th>{t("stock.products.warehouse")}</th>
                                                                    <th>{t("stock.products.available_qty")}</th>
                                                                    <th>{t("stock.products.avg_cost")}</th>
                                                                    <th>{t("stock.products.total_value")}</th>
                                                                    <th>{t("stock.products.last_updated")}</th>
                                                                </tr>
                                                            </thead>
                                                            <tbody>
                                                                {breakdownData && breakdownData.map((wh, idx) => (
                                                                    <tr key={idx}>
                                                                        <td>{wh.warehouse_name}</td>
                                                                        <td>{formatNumber(wh.quantity)}</td>
                                                                        <td style={{ fontWeight: 'bold' }}>{formatNumber(wh.average_cost)} {currency}</td>
                                                                        <td>{formatNumber(wh.total_value)} {currency}</td>
                                                                        <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                                                                            {wh.last_update ? formatShortDate(wh.last_update) : '-'}
                                                                        </td>
                                                                    </tr>
                                                                ))}
                                                                {(!breakdownData || breakdownData.length === 0) && (
                                                                    <tr><td colSpan="5" className="text-center">{t("stock.products.no_stock_data")}</td></tr>
                                                                )}
                                                            </tbody>
                                                        </table>
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    )}
                                </React.Fragment>
                            ))
                        )}
                    </tbody>
                </table>
                <Pagination currentPage={currentPage} totalItems={totalItems} pageSize={pageSize} onPageChange={onPageChange} onPageSizeChange={onPageSizeChange} />
            </div>

            {/* Delete Confirmation Modal */}
            {showDeleteModal && (
                <div className="modal-overlay" onClick={() => setShowDeleteModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '450px' }}>
                        <div className="modal-header">
                            <h2 style={{ color: 'var(--danger)' }}>⚠️ {t('common.confirm_delete')}</h2>
                            <button onClick={() => setShowDeleteModal(false)} className="close-btn">&times;</button>
                        </div>
                        <div style={{ padding: '1rem 0' }}>
                            <p>{t('stock.products.delete_confirm_message', { name: productToDelete?.name })}</p>
                            <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '8px' }}>
                                {t('common.action_cannot_be_undone')}
                            </p>
                        </div>
                        <div className="modal-actions" style={{ marginTop: '1.5rem' }}>
                            <button onClick={() => setShowDeleteModal(false)} className="btn btn-secondary">
                                {t('common.cancel')}
                            </button>
                            <button onClick={handleDeleteConfirm} className="btn btn-danger">
                                {t('common.delete')}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <style>{`
                .modal-overlay {
                    position: fixed;
                    top: 0; left: 0; right: 0; bottom: 0;
                    background: rgba(0,0,0,0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                }
                .modal-content {
                    background: white;
                    padding: 1.5rem;
                    border-radius: 12px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                }
                .modal-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 1rem;
                }
                .close-btn {
                    background: none;
                    border: none;
                    font-size: 1.5rem;
                    cursor: pointer;
                    color: var(--text-secondary);
                }
                .modal-actions {
                    display: flex;
                    justify-content: flex-end;
                    gap: 0.75rem;
                }
                .btn-danger {
                    background-color: var(--danger);
                    color: white;
                    border: none;
                    padding: 0.5rem 1.5rem;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 500;
                }
                .btn-danger:hover {
                    opacity: 0.9;
                }
            `}</style>
        </div >
    )
}

export default ProductList

