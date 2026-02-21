import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Factory, Layers, Package, Play, CheckCircle, Clock, Plus, ArrowLeft, DollarSign, TrendingUp } from 'lucide-react'
import api from '../../utils/api'
import { formatNumber } from '../../utils/format'
import { formatShortDate } from '../../utils/dateUtils'
import '../../components/ModuleStyles.css'

export default function ManufacturingDashboard() {
    const { t, i18n } = useTranslation()
    const navigate = useNavigate()
    const isRTL = i18n.language === 'ar'

    const [stats, setStats] = useState(null)
    const [orders, setOrders] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchData()
    }, [])

    const fetchData = async () => {
        try {
            setLoading(true)
            const [statsRes, ordersRes] = await Promise.all([
                api.get('/manufacturing/dashboard/stats'),
                api.get('/manufacturing/orders')
            ])
            setStats(statsRes.data)
            setOrders(ordersRes.data)
        } catch (err) {
            console.error('Failed to fetch manufacturing data', err)
        } finally {
            setLoading(false)
        }
    }

    if (loading) return <div className="page-center"><span className="loading"></span></div>

    const getStatusBadge = (s) => {
        switch (s) {
            case 'completed': return 'badge-success'
            case 'in_progress': return 'badge-warning'
            case 'draft': return 'badge'
            case 'cancelled': return 'badge-danger'
            default: return 'badge'
        }
    }

    return (
        <div className="workspace fade-in">
            {/* Header */}
            <div className="workspace-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className="workspace-title" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <span style={{ padding: '8px', borderRadius: '12px', background: '#fff8e1' }}>
                                <Factory size={24} style={{ color: '#d97706' }} />
                            </span>
                            {t('manufacturing.title') || 'التصنيع'}
                        </h1>
                        <p className="workspace-subtitle">
                            {t('manufacturing.dashboard.subtitle') || 'إدارة عمليات التصنيع والإنتاج'}
                        </p>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                        <button className="btn btn-secondary" onClick={() => navigate('/manufacturing/boms')}>
                            <Layers size={16} /> {t('manufacturing.bom_list') || 'قوائم المواد'}
                        </button>
                        <button className="btn btn-primary" onClick={() => navigate('/manufacturing/orders/new')}>
                            <Plus size={16} /> {t('manufacturing.new_order') || 'أمر تصنيع جديد'}
                        </button>
                    </div>
                </div>
            </div>

            {/* Stats Cards */}
            {stats && (
                <div className="metrics-grid mb-4">
                    <div className="metric-card" style={{ cursor: 'pointer' }} onClick={() => navigate('/manufacturing/orders')}>
                        <div className="metric-icon" style={{ background: '#e3f2fd' }}>
                            <Factory size={20} style={{ color: '#1565c0' }} />
                        </div>
                        <div className="metric-content">
                            <span className="metric-label">{t('manufacturing.dashboard.total_orders') || 'إجمالي الأوامر'}</span>
                            <span className="metric-value">{stats.orders.total}</span>
                        </div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-icon" style={{ background: '#fff8e1' }}>
                            <Clock size={20} style={{ color: '#f59e0b' }} />
                        </div>
                        <div className="metric-content">
                            <span className="metric-label">{t('manufacturing.dashboard.in_progress') || 'قيد التنفيذ'}</span>
                            <span className="metric-value" style={{ color: '#f59e0b' }}>{stats.orders.in_progress}</span>
                        </div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-icon" style={{ background: '#e8f5e9' }}>
                            <CheckCircle size={20} style={{ color: '#2e7d32' }} />
                        </div>
                        <div className="metric-content">
                            <span className="metric-label">{t('manufacturing.dashboard.completed')}</span>
                            <span className="metric-value" style={{ color: '#2e7d32' }}>{stats.orders.completed}</span>
                        </div>
                    </div>
                    <div className="metric-card" style={{ cursor: 'pointer' }} onClick={() => navigate('/manufacturing/boms')}>
                        <div className="metric-icon" style={{ background: '#f3e5f5' }}>
                            <Layers size={20} style={{ color: '#7b1fa2' }} />
                        </div>
                        <div className="metric-content">
                            <span className="metric-label">{t('manufacturing.dashboard.active_boms') || 'قوائم المواد النشطة'}</span>
                            <span className="metric-value">{stats.boms.active}</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Last 30 Days Stats */}
            {stats && (
                <div className="metrics-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
                    <div className="metric-card">
                        <div className="metric-icon" style={{ background: '#e8f5e9' }}>
                            <TrendingUp size={20} style={{ color: '#2e7d32' }} />
                        </div>
                        <div className="metric-content">
                            <span className="metric-label">{t('manufacturing.dashboard.production_30d')}</span>
                            <span className="metric-value">{formatNumber(stats.last_30_days.production_volume)} <small>{t('common.unit')}</small></span>
                        </div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-icon" style={{ background: '#fff3e0' }}>
                            <DollarSign size={20} style={{ color: '#e65100' }} />
                        </div>
                        <div className="metric-content">
                            <span className="metric-label">{t('manufacturing.dashboard.material_cost_30d')}</span>
                            <span className="metric-value">{formatNumber(stats.last_30_days.material_cost)}</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Recent Orders */}
            <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h3 className="section-title" style={{ margin: 0 }}>
                        {t('manufacturing.dashboard.recent_orders') || 'أوامر الإنتاج الأخيرة'}
                    </h3>
                    <button className="btn btn-secondary btn-sm" onClick={() => navigate('/manufacturing/orders')}>
                        {t('common.view_all') || 'عرض الكل'} →
                    </button>
                </div>
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>{t('manufacturing.bom') || 'قائمة المواد'}</th>
                            <th>{t('manufacturing.quantity') || 'الكمية'}</th>
                            <th>{t('common.start_date') || 'تاريخ البدء'}</th>
                            <th>{t('common.status') || 'الحالة'}</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        {orders.length === 0 ? (
                            <tr>
                                <td colSpan="6" style={{ textAlign: 'center', padding: '40px', color: '#888' }}>
                                    <Package size={40} style={{ margin: '0 auto 12px', display: 'block', opacity: 0.3 }} />
                                    <p>{t('manufacturing.no_orders') || 'لا توجد أوامر تصنيع'}</p>
                                    <button className="btn btn-primary btn-sm mt-4" onClick={() => navigate('/manufacturing/orders/new')}>
                                        <Plus size={14} /> {t('manufacturing.new_order') || 'أمر تصنيع جديد'}
                                    </button>
                                </td>
                            </tr>
                        ) : (
                            orders.slice(0, 10).map(order => (
                                <tr key={order.id} onClick={() => navigate(`/manufacturing/orders/${order.id}`)} style={{ cursor: 'pointer' }}>
                                    <td style={{ fontWeight: 'bold' }}>{order.id}</td>
                                    <td>{order.bom_name}</td>
                                    <td><span style={{ background: 'var(--bg-secondary)', borderRadius: '6px', padding: '2px 8px', fontSize: '12px', fontWeight: 600 }}>{order.quantity}</span></td>
                                    <td>{order.start_date ? formatShortDate(order.start_date) : '—'}</td>
                                    <td>
                                        <span className={`badge ${getStatusBadge(order.status)}`}>
                                            {t(`manufacturing.status.${order.status}`) || order.status}
                                        </span>
                                    </td>
                                    <td>
                                        <button className="table-action-btn">
                                            <ArrowLeft size={14} />
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Recent Completed */}
            {stats && stats.recent_completed.length > 0 && (
                <div className="card mt-4">
                    <h3 className="section-title">{t('manufacturing.dashboard.recently_completed') || 'الأوامر المكتملة مؤخراً'}</h3>
                    <div style={{ display: 'grid', gap: '8px' }}>
                        {stats.recent_completed.map(r => (
                            <div key={r.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', background: '#f8faf8', borderRadius: '8px', border: '1px solid #e8f5e9' }}
                                onClick={() => navigate(`/manufacturing/orders/${r.id}`)} className="hover-card">
                                <div>
                                    <span style={{ fontWeight: 'bold' }}>{r.product_name}</span>
                                    <span style={{ color: '#888', marginRight: '8px', marginLeft: '8px' }}>({r.bom_name})</span>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                                    <span style={{ background: 'var(--bg-secondary)', borderRadius: '6px', padding: '2px 8px', fontSize: '12px', fontWeight: 600 }}>{formatNumber(r.quantity)} {t('manufacturing.cycles') || 'دورة'}</span>
                                    {r.end_date && <span style={{ color: '#888', fontSize: '0.85rem' }}>{formatShortDate(r.end_date)}</span>}
                                    <CheckCircle size={16} style={{ color: '#2e7d32' }} />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
