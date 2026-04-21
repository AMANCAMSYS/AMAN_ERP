import { useState, useEffect } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ArrowRight, ArrowLeft, Play, CheckCircle, XCircle, Factory, Package, DollarSign, AlertTriangle, Clock } from 'lucide-react'
import api from '../../utils/api'
import { toastEmitter } from '../../utils/toastEmitter'
import { formatNumber, formatCurrency } from '../../utils/format'
import { formatShortDate } from '../../utils/dateUtils'
import { useToast } from '../../context/ToastContext'
import SimpleModal from '../../components/common/SimpleModal'
import '../../components/ModuleStyles.css'
import BackButton from '../../components/common/BackButton';
import { PageLoading } from '../../components/common/LoadingStates'

export default function ProductionOrderDetails() {
    const { t, i18n } = useTranslation()
    const navigate = useNavigate()
    const { id } = useParams()
    const { showToast } = useToast()
    const isRTL = i18n.language === 'ar'

    const [order, setOrder] = useState(null)
    const [loading, setLoading] = useState(true)
    const [actionLoading, setActionLoading] = useState(false)
    const [showCompleteModal, setShowCompleteModal] = useState(false)
    const [showCancelModal, setShowCancelModal] = useState(false)

    useEffect(() => { fetchOrder() }, [id])

    const fetchOrder = async () => {
        try {
            setLoading(true)
            const res = await api.get(`/manufacturing/orders/${id}`)
            setOrder(res.data)
        } catch (err) {
            toastEmitter.emit(t('common.error'), 'error')
            showToast(t('manufacturing.details.load_error'), 'error')
        } finally {
            setLoading(false)
        }
    }

    const handleStart = async () => {
        setActionLoading(true)
        try {
            await api.post(`/manufacturing/orders/${id}/start`)
            showToast(t('manufacturing.details.started'), 'success')
            fetchOrder()
        } catch (err) {
            showToast(err.response?.data?.detail || t('common.error_occurred'), 'error')
        } finally {
            setActionLoading(false)
        }
    }

    const handleComplete = async () => {
        setActionLoading(true)
        try {
            await api.post(`/manufacturing/orders/${id}/complete`)
            showToast(t('manufacturing.order_completed'), 'success')
            setShowCompleteModal(false)
            fetchOrder()
        } catch (err) {
            showToast(err.response?.data?.detail || t('common.error_occurred'), 'error')
        } finally {
            setActionLoading(false)
        }
    }

    const handleCancel = async () => {
        setActionLoading(true)
        try {
            await api.post(`/manufacturing/orders/${id}/cancel`)
            showToast(t('manufacturing.details.cancelled'), 'success')
            setShowCancelModal(false)
            fetchOrder()
        } catch (err) {
            showToast(err.response?.data?.detail || t('common.error_occurred'), 'error')
        } finally {
            setActionLoading(false)
        }
    }

    if (loading) {
        return (
            <div className="workspace flex items-center justify-center fade-in">
                <div className="text-center">
                    <PageLoading />
                    <p className="text-slate-500">{t('common.loading')}</p>
                </div>
            </div>
        )
    }

    if (!order) {
        return (
            <div className="workspace fade-in">
                <div className="text-center" style={{ padding: '80px 0' }}>
                    <div style={{ fontSize: '48px', marginBottom: '16px' }}>🏭</div>
                    <h3 style={{ color: '#666', marginBottom: '8px' }}>{t('manufacturing.details.not_found')}</h3>
                    <button className="btn btn-primary mt-3" onClick={() => navigate('/manufacturing/orders')}>
                        {isRTL ? <ArrowRight size={16} /> : <ArrowLeft size={16} />}
                        {t('manufacturing.details.back_to_list')}
                    </button>
                </div>
            </div>
        )
    }

    const getStatusBadge = (s) => {
        const map = {
            completed: { cls: 'bg-success-subtle text-success', icon: <CheckCircle size={14} /> },
            in_progress: { cls: 'bg-warning-subtle text-warning', icon: <Clock size={14} /> },
            draft: { cls: 'bg-secondary-subtle text-secondary', icon: '📝' },
            cancelled: { cls: 'bg-danger-subtle text-danger', icon: <XCircle size={14} /> }
        }
        const badge = map[s] || map.draft
        return (
            <span className={`badge ${badge.cls}`} style={{ padding: '6px 14px', fontSize: '13px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                {badge.icon} {t(`manufacturing.status.${s}`, s)}
            </span>
        )
    }

    const isActionable = order.status !== 'completed' && order.status !== 'cancelled'

    return (
        <div className="workspace fade-in">
            {/* Header */}
            <div className="workspace-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                        <BackButton />
                        <div>
                            <h1 className="workspace-title" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <span style={{ padding: '8px', borderRadius: '12px', background: '#fff8e1' }}>
                                    <Factory size={24} style={{ color: '#d97706' }} />
                                </span>
                                {t('manufacturing.details.title')} #{order.id}
                                {getStatusBadge(order.status)}
                            </h1>
                            <p className="text-muted small mb-0" style={{ marginTop: '4px' }}>
                                {order.bom_name} — {order.product_name}
                            </p>
                        </div>
                    </div>
                    {isActionable && (
                        <div style={{ display: 'flex', gap: '8px' }}>
                            {order.status === 'draft' && (
                                <button className="btn btn-primary" onClick={handleStart} disabled={actionLoading} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <Play size={16} /> {t('manufacturing.start_production')}
                                </button>
                            )}
                            {(order.status === 'in_progress' || order.status === 'draft') && (
                                <button
                                    className="btn btn-success"
                                    onClick={() => setShowCompleteModal(true)}
                                    disabled={actionLoading || !order.all_materials_sufficient}
                                    title={!order.all_materials_sufficient ? t('manufacturing.details.insufficient_materials') : ''}
                                    style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
                                >
                                    <CheckCircle size={16} /> {t('manufacturing.complete_production')}
                                </button>
                            )}
                            <button
                                className="btn btn-warning"
                                onClick={() => navigate(`/manufacturing/mrp/${id}`)}
                                style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
                            >
                                <AlertTriangle size={16} /> {t('manufacturing.mrp.title')}
                            </button>
                            <button className="btn btn-outline-danger" onClick={() => setShowCancelModal(true)} disabled={actionLoading} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <XCircle size={16} /> {t('common.cancel')}
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* Insufficient Materials Warning */}
            {isActionable && !order.all_materials_sufficient && (
                <div style={{ background: '#fff3cd', border: '1px solid #ffc107', borderRadius: '12px', padding: '12px 16px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '10px', color: '#856404' }}>
                    <AlertTriangle size={18} />
                    <span>{t('manufacturing.details.materials_warning')}</span>
                </div>
            )}

            {/* Summary Cards */}
            <div className="row g-3 mb-4">
                <div className="col-md-3">
                    <div className="card card-compact h-100">
                        <div className="d-flex align-items-center gap-3">
                            <div style={{ padding: '10px', borderRadius: '12px', background: '#fff8e1' }}>
                                <Factory size={22} style={{ color: '#f59e0b' }} />
                            </div>
                            <div>
                                <div className="text-muted small">{t('manufacturing.cycles')}</div>
                                <div className="fw-bold fs-5">{formatNumber(order.quantity)}</div>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="col-md-3">
                    <div className="card card-compact h-100">
                        <div className="d-flex align-items-center gap-3">
                            <div style={{ padding: '10px', borderRadius: '12px', background: '#e8f5e9' }}>
                                <Package size={22} style={{ color: '#2e7d32' }} />
                            </div>
                            <div>
                                <div className="text-muted small">{t('manufacturing.total_output')}</div>
                                <div className="fw-bold fs-5">{formatNumber(order.total_output)}</div>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="col-md-3">
                    <div className="card card-compact h-100">
                        <div className="d-flex align-items-center gap-3">
                            <div style={{ padding: '10px', borderRadius: '12px', background: '#e3f2fd' }}>
                                <DollarSign size={22} style={{ color: '#1565c0' }} />
                            </div>
                            <div>
                                <div className="text-muted small">{t('manufacturing.details.total_cost')}</div>
                                <div className="fw-bold fs-5">{formatNumber(order.total_material_cost)}</div>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="col-md-3">
                    <div className="card card-compact h-100">
                        <div className="d-flex align-items-center gap-3">
                            <div style={{ padding: '10px', borderRadius: '12px', background: '#fce4ec' }}>
                                <DollarSign size={22} style={{ color: '#c62828' }} />
                            </div>
                            <div>
                                <div className="text-muted small">{t('manufacturing.details.unit_cost')}</div>
                                <div className="fw-bold fs-5">{formatNumber(order.unit_production_cost)}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Order Info + Cost Breakdown */}
            <div className="row g-3 mb-4">
                <div className="col-md-6">
                    <div className="card card-compact h-100">
                        <div >
                            <h6 className="fw-bold mb-3" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                📋 {t('manufacturing.details.order_info')}
                            </h6>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                                <div>
                                    <div className="text-muted small mb-1">{t('manufacturing.bom')}</div>
                                    <div className="fw-semibold">{order.bom_name}</div>
                                </div>
                                <div>
                                    <div className="text-muted small mb-1">{t('manufacturing.product')}</div>
                                    <div className="fw-semibold">{order.product_name}</div>
                                </div>
                                <div>
                                    <div className="text-muted small mb-1">{t('common.start_date')}</div>
                                    <div className="fw-semibold">{order.start_date ? formatShortDate(order.start_date) : '—'}</div>
                                </div>
                                <div>
                                    <div className="text-muted small mb-1">{t('common.end_date')}</div>
                                    <div className="fw-semibold">{order.end_date ? formatShortDate(order.end_date) : '—'}</div>
                                </div>
                                <div>
                                    <div className="text-muted small mb-1">{t('common.created_at')}</div>
                                    <div className="fw-semibold">{order.created_at ? formatShortDate(order.created_at) : '—'}</div>
                                </div>
                                <div>
                                    <div className="text-muted small mb-1">{t('manufacturing.quantity')}</div>
                                    <div className="fw-semibold">{formatNumber(order.quantity)}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="col-md-6">
                    <div className="card card-compact h-100">
                        <div >
                            <h6 className="fw-bold mb-3" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                💰 {t('manufacturing.details.cost_breakdown')}
                            </h6>
                            <div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #f0f0f0' }}>
                                    <span className="text-muted">{t('manufacturing.details.material_count')}</span>
                                    <span className="fw-bold">{order.materials.length}</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #f0f0f0' }}>
                                    <span className="text-muted">{t('manufacturing.details.total_material_cost')}</span>
                                    <span className="fw-bold">{formatNumber(order.total_material_cost)}</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #f0f0f0' }}>
                                    <span className="text-muted">{t('manufacturing.details.material_cost')}</span>
                                    <span className="fw-bold">{formatCurrency((order.total_material_cost || 0))}</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #f0f0f0' }}>
                                    <span className="text-muted">{t('manufacturing.details.labor_overhead_cost')}</span>
                                    <span className="fw-bold">{formatCurrency((order.total_labor_overhead_cost || 0))}</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #f0f0f0' }}>
                                    <span className="text-muted">{t('manufacturing.details.total_cost')}</span>
                                    <span className="fw-bold text-success">{formatCurrency((order.total_production_cost || 0))}</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #f0f0f0' }}>
                                    <span className="text-muted">{t('manufacturing.total_output')}</span>
                                    <span className="fw-bold">{formatNumber(order.total_output)}</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '14px 0', fontWeight: 'bold', fontSize: '1.05rem' }}>
                                    <span>{t('manufacturing.details.unit_cost')}</span>
                                    <span style={{ color: 'var(--primary, #3b82f6)' }}>{formatNumber(order.unit_production_cost)}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Raw Materials Table */}
            <div className="card card-flush mb-4">
                <div className="p-4 pb-0">
                    <h6 className="fw-bold mb-0" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        📦 {t('manufacturing.raw_materials')}
                        <span className="badge bg-primary-subtle text-primary rounded-pill">{order.materials.length}</span>
                    </h6>
                </div>
                <div className="table-responsive">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th style={{ paddingRight: '16px', paddingLeft: '16px' }}>#</th>
                                <th>{t('manufacturing.material_name')}</th>
                                <th className="text-center">{t('manufacturing.details.bom_qty')}</th>
                                <th className="text-center">{t('manufacturing.details.total_needed')}</th>
                                <th className="text-center">{t('manufacturing.waste')} %</th>
                                <th className="text-center">{t('manufacturing.details.unit_cost_label')}</th>
                                <th className="text-center">{t('manufacturing.details.line_cost')}</th>
                                <th className="text-center">{t('manufacturing.details.available')}</th>
                                <th className="text-center">{t('common.status_title')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {order.materials.map((m, idx) => (
                                <tr key={m.item_id}>
                                    <td style={{ paddingRight: '16px', paddingLeft: '16px' }}>{idx + 1}</td>
                                    <td>
                                        <div className="fw-bold">{m.item_name}</div>
                                        {m.unit && <div className="text-muted small">{m.unit}</div>}
                                    </td>
                                    <td className="text-center">{formatNumber(m.bom_quantity)}</td>
                                    <td className="text-center fw-semibold">{formatNumber(m.total_quantity_needed)}</td>
                                    <td className="text-center">{m.waste_percentage}%</td>
                                    <td className="text-center">{formatNumber(m.unit_cost)}</td>
                                    <td className="text-center fw-bold">{formatNumber(m.total_cost)}</td>
                                    <td className="text-center">{formatNumber(m.available_stock)}</td>
                                    <td className="text-center">
                                        {m.sufficient ? (
                                            <span className="badge bg-success-subtle text-success" style={{ padding: '4px 10px' }}>
                                                ✓ {t('manufacturing.details.sufficient')}
                                            </span>
                                        ) : (
                                            <span className="badge bg-danger-subtle text-danger" style={{ padding: '4px 10px' }}>
                                                ✗ {t('manufacturing.details.insufficient')}
                                            </span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Operations / Job Cards */}
            <div className="card card-flush mb-4">
                <div className="p-4 pb-0 d-flex justify-content-between">
                    <h6 className="fw-bold mb-0" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        ⚙️ {t('manufacturing.operations')}
                    </h6>
                    <Link to="/manufacturing/job-cards" className="text-primary small fw-bold">
                        {t('manufacturing.view_all_job_cards')}
                    </Link>
                </div>
                <div className="table-responsive">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th style={{ paddingRight: '16px', paddingLeft: '16px' }}>{t('common.sequence')}</th>
                                <th>{t('manufacturing.operation')}</th>
                                <th>{t('manufacturing.work_center')}</th>
                                <th>{t('common.status_title')}</th>
                                <th className="text-center">{t('common.actions')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {order.operations && order.operations.length > 0 ? order.operations.map(op => (
                                <tr key={op.id}>
                                    <td style={{ paddingRight: '16px', paddingLeft: '16px' }}>{op.sequence}</td>
                                    <td>
                                        <div className="fw-bold">{op.operation_description || op.operation_name}</div>
                                        {op.start_time && <div className="text-muted extra-small">Started: {new Date(op.start_time).toLocaleString()}</div>}
                                    </td>
                                    <td>{op.work_center_name}</td>
                                    <td>{getStatusBadge(op.status)}</td>
                                    <td className="text-center">
                                        <div className="d-flex gap-2 justify-content-center">
                                            {op.status !== 'in_progress' && op.status !== 'completed' && (
                                                <button className="table-action-btn text-primary" onClick={() => navigate('/manufacturing/job-cards')}>
                                                    <Play size={16} />
                                                </button>
                                            )}
                                            {op.status === 'in_progress' && (
                                                <button className="table-action-btn text-warning" onClick={() => navigate('/manufacturing/job-cards')}>
                                                    <Clock size={16} />
                                                </button>
                                            )}
                                            {op.status === 'completed' && <CheckCircle size={18} className="text-success" />}
                                        </div>
                                    </td>
                                </tr>
                            )) : (
                                <tr>
                                    <td colSpan="5" className="text-center text-muted py-4">
                                        {t('manufacturing.no_operations')}
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Inventory Transactions */}
            {order.transactions && order.transactions.length > 0 && (
                <div className="card card-flush">
                    <div className="p-4 pb-0">
                        <h6 className="fw-bold mb-0" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            📊 {t('manufacturing.details.inventory_movements')}
                        </h6>
                    </div>
                    <div className="table-responsive">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>{t('manufacturing.product')}</th>
                                    <th className="text-center">{t('manufacturing.details.movement_type')}</th>
                                    <th className="text-center">{t('manufacturing.quantity')}</th>
                                    <th className="text-center">{t('manufacturing.details.unit_cost_label')}</th>
                                    <th className="text-center">{t('manufacturing.details.line_cost')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {order.transactions.map(txn => (
                                    <tr key={txn.id}>
                                        <td className="fw-medium">{txn.product_name}</td>
                                        <td className="text-center">
                                            <span className={`badge ${txn.transaction_type === 'manufacturing_output' ? 'bg-success-subtle text-success' : 'bg-warning-subtle text-warning'}`} style={{ padding: '4px 10px' }}>
                                                {txn.transaction_type === 'manufacturing_output'
                                                    ? t('manufacturing.details.output_type')
                                                    : t('manufacturing.details.consume_type')}
                                            </span>
                                        </td>
                                        <td className="text-center" style={{ color: txn.quantity < 0 ? '#c62828' : '#2e7d32', fontWeight: '600' }}>
                                            {txn.quantity > 0 ? '+' : ''}{formatNumber(txn.quantity)}
                                        </td>
                                        <td className="text-center">{formatNumber(txn.unit_cost)}</td>
                                        <td className="text-center fw-bold">{formatNumber(txn.total_cost)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Complete Modal */}
            {showCompleteModal && (
                <SimpleModal
                    title={t('manufacturing.complete_production')}
                    onClose={() => setShowCompleteModal(false)}
                >
                    <p style={{ marginBottom: '12px' }}>
                        {t('manufacturing.details.complete_confirm')}
                    </p>
                    <div style={{ background: '#f8f9fa', padding: '14px', borderRadius: '10px', marginBottom: '16px' }}>
                        <p style={{ margin: '4px 0' }}><strong>{t('manufacturing.product')}:</strong> {order.product_name}</p>
                        <p style={{ margin: '4px 0' }}><strong>{t('manufacturing.total_output')}:</strong> {formatNumber(order.total_output)} {t('manufacturing.unit')}</p>
                        <p style={{ margin: '4px 0' }}><strong>{t('manufacturing.details.total_cost')}:</strong> {formatNumber(order.total_material_cost)}</p>
                    </div>
                    <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                        <button className="btn btn-secondary" onClick={() => setShowCompleteModal(false)} disabled={actionLoading}>
                            {t('common.close')}
                        </button>
                        <button className="btn btn-success" onClick={handleComplete} disabled={actionLoading}>
                            {actionLoading ? '...' : t('manufacturing.details.confirm_complete')}
                        </button>
                    </div>
                </SimpleModal>
            )}

            {/* Cancel Modal */}
            {showCancelModal && (
                <SimpleModal
                    title={t('manufacturing.details.cancel_title')}
                    onClose={() => setShowCancelModal(false)}
                >
                    <p style={{ marginBottom: '16px' }}>
                        {t('manufacturing.details.cancel_confirm')}
                    </p>
                    <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                        <button className="btn btn-secondary" onClick={() => setShowCancelModal(false)} disabled={actionLoading}>
                            {t('common.close')}
                        </button>
                        <button className="btn btn-danger" onClick={handleCancel} disabled={actionLoading}>
                            {actionLoading ? '...' : t('manufacturing.details.confirm_cancel')}
                        </button>
                    </div>
                </SimpleModal>
            )}
        </div>
    )
}
