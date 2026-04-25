import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { manufacturingAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import { formatNumber } from '../../utils/format';
import {
    FaIndustry, FaRoute, FaLayerGroup, FaClipboardList, FaCogs, FaChartLine, FaPlus, FaIdCard, FaBoxes, FaTools, FaCalendarAlt
} from 'react-icons/fa';
import '../../components/ModuleStyles.css';
import { formatDate } from '../../utils/dateUtils';
import { PageLoading } from '../../components/common/LoadingStates'

const ManufacturingHome = () => {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const [stats, setStats] = useState({
        workCenters: 0,
        routes: 0,
        boms: 0,
        orders: [],
        activeOrders: 0,
        completedOrders: 0
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const [wc, r, b, o] = await Promise.all([
                    manufacturingAPI.listWorkCenters(),
                    manufacturingAPI.listRoutes(),
                    manufacturingAPI.listBOMs(),
                    manufacturingAPI.listOrders()
                ]);

                const active = o.data.filter(ord => ord.status !== 'completed' && ord.status !== 'cancelled').length;
                const completed = o.data.filter(ord => ord.status === 'completed').length;

                setStats({
                    workCenters: wc.data.length,
                    routes: r.data.length,
                    boms: b.data.length,
                    orders: o.data,
                    activeOrders: active,
                    completedOrders: completed
                });
            } catch (error) {
                toastEmitter.emit(t('common.error'), 'error');
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, []);

    const getStatusBadge = (status) => {
        const map = {
            draft: { label: t('draft'), bg: 'rgb(254, 243, 199)', color: 'rgb(217, 119, 6)', emoji: '⏳' },
            planned: { label: t('planned'), bg: 'rgba(59, 130, 246, 0.1)', color: 'rgb(59, 130, 246)', emoji: '📅' },
            confirmed: { label: t('confirmed'), bg: 'rgb(224, 231, 255)', color: 'rgb(67, 56, 202)', emoji: '👍' },
            in_progress: { label: t('in_progress'), bg: 'rgb(254, 249, 195)', color: 'rgb(161, 98, 7)', emoji: '⚙️' },
            completed: { label: t('completed'), bg: 'rgb(220, 252, 231)', color: 'rgb(22, 163, 74)', emoji: '✅' },
            cancelled: { label: t('cancelled'), bg: 'rgb(254, 226, 226)', color: 'rgb(220, 38, 38)', emoji: '❌' }
        };
        const s = map[status] || { label: status, bg: 'rgba(107, 114, 128, 0.082)', color: 'rgb(107, 114, 128)', emoji: '' };
        return (
            <span style={{ background: s.bg, color: s.color, padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '600', whiteSpace: 'nowrap' }}>
                {s.emoji} {s.label}
            </span>
        );
    };

    if (loading) return <PageLoading />;

    return (
        <div className="workspace fade-in">
            {/* Header */}
            <div className="workspace-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                    <div>
                        <h1 className="workspace-title flex items-center gap-2">
                            <FaCogs /> {t('manufacturing.title')}
                        </h1>
                        <p className="workspace-subtitle">{t('manufacturing.dashboard.subtitle')}</p>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                        <button className="btn btn-primary" onClick={() => navigate('/manufacturing/orders')}>
                            <FaPlus /> {t('manufacturing.new_order')}
                        </button>
                    </div>
                </div>
            </div>

            {/* Metrics Grid */}
            <div className="metrics-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
                <div className="metric-card">
                    <div className="metric-label">{t('manufacturing.active_orders')}</div>
                    <div className="metric-value text-blue-600">{stats.activeOrders}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('manufacturing.completed_orders')}</div>
                    <div className="metric-value text-green-600">{stats.completedOrders}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('manufacturing.work_centers')}</div>
                    <div className="metric-value">{stats.workCenters}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('manufacturing.routes')}</div>
                    <div className="metric-value">{stats.routes}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('manufacturing.active_boms')}</div>
                    <div className="metric-value">{stats.boms}</div>
                </div>
            </div>

            {/* Navigation */}
            <div className="mt-4">
                    {/* Grouped Navigation Cards */}
                    <div className="modules-grid" style={{ gap: '16px', marginBottom: '20px' }}>

                        {/* Production & Orders */}
                        <div className="card">
                            <h3 className="section-title section-title-icon">
                                <FaClipboardList style={{ color: 'var(--primary)' }} /> {t('manufacturing.production', 'الإنتاج والأوامر')}
                            </h3>
                            <div className="manufacturing-links-grid">
                                <Link to="/manufacturing/orders" className="btn btn-outline manufacturing-nav-link">
                                    <FaClipboardList /> {t('manufacturing.manage_orders')}
                                </Link>
                                <Link to="/manufacturing/job-cards" className="btn btn-outline manufacturing-nav-link">
                                    <FaIdCard /> {t('manufacturing.job_cards.title')}
                                </Link>
                                <Link to="/manufacturing/mrp" className="btn btn-outline manufacturing-nav-link">
                                    <FaBoxes /> {t('manufacturing.mrp.title')}
                                </Link>
                                <Link to="/manufacturing/schedule" className="btn btn-outline manufacturing-nav-link">
                                    <FaCalendarAlt /> {t('manufacturing.production_schedule')}
                                </Link>
                                <Link to="/manufacturing/shopfloor" className="btn btn-outline manufacturing-nav-link">
                                    ⚙️ {t('nav.shop_floor')}
                                </Link>
                            </div>
                        </div>

                        {/* Master Data */}
                        <div className="card">
                            <h3 className="section-title section-title-icon">
                                <FaCogs style={{ color: 'var(--secondary)' }} /> {t('manufacturing.master_data', 'البيانات الأساسية')}
                            </h3>
                            <div className="manufacturing-links-grid">
                                <Link to="/manufacturing/work-centers" className="btn btn-outline manufacturing-nav-link">
                                    <FaIndustry /> {t('manufacturing.manage_work_centers')}
                                </Link>
                                <Link to="/manufacturing/routes" className="btn btn-outline manufacturing-nav-link">
                                    <FaRoute /> {t('manufacturing.manage_routes')}
                                </Link>
                                <Link to="/manufacturing/boms" className="btn btn-outline manufacturing-nav-link">
                                    <FaLayerGroup /> {t('manufacturing.manage_boms')}
                                </Link>
                                <Link to="/manufacturing/equipment" className="btn btn-outline manufacturing-nav-link">
                                    <FaTools /> {t('manufacturing.equipment_maintenance')}
                                </Link>
                            </div>
                        </div>

                        {/* Reports */}
                        <div className="card">
                            <h3 className="section-title section-title-icon">
                                <FaChartLine style={{ color: 'var(--success)' }} /> {t('common.reports', 'التقارير')}
                            </h3>
                            <div className="manufacturing-links-grid manufacturing-links-grid-single">
                                <Link to="/manufacturing/reports/direct-labor" className="btn btn-outline manufacturing-nav-link">
                                    👷 {t('manufacturing.direct_labor.title', 'تقرير العمالة المباشرة')}
                                </Link>
                                <Link to="/manufacturing/reports/analytics" className="btn btn-outline manufacturing-nav-link">
                                    📊 {t('manufacturing.analytics.title', 'تحليل الإنتاج')}
                                </Link>
                                <Link to="/manufacturing/reports/work-orders" className="btn btn-outline manufacturing-nav-link">
                                    📋 {t('manufacturing.work_orders_report.title', 'حالة أوامر العمل')}
                                </Link>
                                <Link to="/manufacturing/capacity" className="btn btn-outline manufacturing-nav-link">
                                    🏭 {t('manufacturing.capacity_planning', 'تخطيط الطاقة الإنتاجية')}
                                </Link>
                            </div>
                        </div>
                    </div>

                    {/* Recent Orders Table */}
                    <div className="card">
                        <h3 className="section-title">{t('manufacturing.recent_orders')}</h3>
                        {stats.orders.length === 0 ? (
                            <p className="text-muted mt-3 text-center py-8">{t('manufacturing.no_orders')}</p>
                        ) : (
                            <div className="data-table-container mt-3">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>{t('common.id')}</th>
                                            <th>{t('products.product')}</th>
                                            <th>{t('common.quantity')}</th>
                                            <th>{t('common.due_date')}</th>
                                            <th>{t('common.status_title')}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {stats.orders.slice(0, 5).map(order => (
                                            <tr key={order.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/manufacturing/orders/${order.id}`)}>
                                                <td>
                                                    <span className="font-mono text-blue-600 font-bold">{order.order_number}</span>
                                                </td>
                                                <td>{order.product_name}</td>
                                                <td className="font-bold">{order.produced_quantity} / {order.quantity}</td>
                                                <td>{formatDate(order.due_date)}</td>
                                                <td>{getStatusBadge(order.status)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>


        </div>
    );
};

export default ManufacturingHome;
