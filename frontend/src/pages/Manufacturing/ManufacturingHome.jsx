import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { manufacturingAPI } from '../../utils/api';
import { formatNumber } from '../../utils/format';
import {
    FaIndustry, FaRoute, FaLayerGroup, FaClipboardList, FaCogs, FaChartLine, FaArrowRight, FaPlus, FaIdCard, FaBoxes, FaTools, FaCalendarAlt
} from 'react-icons/fa';
import '../../components/ModuleStyles.css';
import { formatDate, formatDateTime } from '../../utils/dateUtils';

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
    const [activeTab, setActiveTab] = useState('overview');

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
                console.error("Error fetching stats:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, []);

    const getStatusBadge = (status) => {
        const map = {
            draft: { label: t('draft') || 'مسودة', bg: 'rgb(254, 243, 199)', color: 'rgb(217, 119, 6)', emoji: '⏳' },
            planned: { label: t('planned') || 'مخطط', bg: 'rgba(59, 130, 246, 0.1)', color: 'rgb(59, 130, 246)', emoji: '📅' },
            confirmed: { label: t('confirmed') || 'مؤكد', bg: 'rgb(224, 231, 255)', color: 'rgb(67, 56, 202)', emoji: '👍' },
            in_progress: { label: t('in_progress') || 'قيد التنفيذ', bg: 'rgb(254, 249, 195)', color: 'rgb(161, 98, 7)', emoji: '⚙️' },
            completed: { label: t('completed') || 'مكتمل', bg: 'rgb(220, 252, 231)', color: 'rgb(22, 163, 74)', emoji: '✅' },
            cancelled: { label: t('cancelled') || 'ملغى', bg: 'rgb(254, 226, 226)', color: 'rgb(220, 38, 38)', emoji: '❌' }
        };
        const s = map[status] || { label: status, bg: 'rgba(107, 114, 128, 0.082)', color: 'rgb(107, 114, 128)', emoji: '' };
        return (
            <span style={{ background: s.bg, color: s.color, padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '600', whiteSpace: 'nowrap' }}>
                {s.emoji} {s.label}
            </span>
        );
    };

    if (loading) return <div className="page-center"><span className="loading"></span></div>;

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
                            <FaPlus /> {t('manufacturing.new_order') || 'أمر تصنيع جديد'}
                        </button>
                    </div>
                </div>
            </div>

            {/* Metrics Grid */}
            <div className="metrics-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
                <div className="metric-card">
                    <div className="metric-label">{t('manufacturing.active_orders') || 'أوامر قيد التنفيذ'}</div>
                    <div className="metric-value text-blue-600">{stats.activeOrders}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('manufacturing.completed_orders') || 'أوامر مكتملة'}</div>
                    <div className="metric-value text-green-600">{stats.completedOrders}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('manufacturing.work_centers')}</div>
                    <div className="metric-value">{stats.workCenters}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('manufacturing.routes') || 'المسارات'}</div>
                    <div className="metric-value">{stats.routes}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('manufacturing.active_boms') || 'قوائم المواد النشطة'}</div>
                    <div className="metric-value">{stats.boms}</div>
                </div>
            </div>

            {/* Tabs */}
            <div className="tabs mt-4">
                {['overview', 'orders'].map(tab => (
                    <button key={tab} className={`tab ${activeTab === tab ? 'active' : ''}`} onClick={() => setActiveTab(tab)}>
                        {tab === 'overview' && (t('manufacturing.dashboard.overview') || 'نظرة عامة')}
                        {tab === 'orders' && (t('manufacturing.production_orders') || 'أوامر التصنيع')}
                    </button>
                ))}
            </div>

            {/* Overview Tab */}
            {activeTab === 'overview' && (
                <div className="mt-4">
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '16px' }}>
                        {/* Quick Actions */}
                        <div className="card">
                            <h3 className="section-title">{t('common.actions') || 'إجراءات سريعة'}</h3>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '12px' }}>
                                <Link to="/manufacturing/orders" className="btn btn-outline" style={{ textAlign: 'center' }}>
                                    <FaClipboardList /> {t('manufacturing.manage_orders') || 'إدارة أوامر التصنيع'}
                                </Link>
                                <Link to="/manufacturing/work-centers" className="btn btn-outline" style={{ textAlign: 'center' }}>
                                    <FaIndustry /> {t('manufacturing.manage_work_centers') || 'إدارة محطات العمل'}
                                </Link>
                                <Link to="/manufacturing/routes" className="btn btn-outline" style={{ textAlign: 'center' }}>
                                    <FaRoute /> {t('manufacturing.manage_routes') || 'إدارة المسارات'}
                                </Link>
                                <Link to="/manufacturing/boms" className="btn btn-outline" style={{ textAlign: 'center' }}>
                                    <FaLayerGroup /> {t('manufacturing.manage_boms') || 'إدارة قوائم المواد'}
                                </Link>
                                <Link to="/manufacturing/job-cards" className="btn btn-outline" style={{ textAlign: 'center', border: '1px dashed #cbd5e1' }}>
                                    <FaIdCard /> {t('manufacturing.job_cards.title', 'بطاقات العمل')}
                                </Link>
                                <Link to="/manufacturing/mrp" className="btn btn-outline" style={{ textAlign: 'center', border: '1px dashed #cbd5e1' }}>
                                    <FaBoxes /> {t('manufacturing.mrp.title', 'تخطيط المتطلبات (MRP)')}
                                </Link>
                                <Link to="/manufacturing/equipment" className="btn btn-outline" style={{ textAlign: 'center', border: '1px dashed #cbd5e1' }}>
                                    <FaTools /> {t('manufacturing.equipment_maintenance', 'المعدات والصيانة')}
                                </Link>
                                <Link to="/manufacturing/schedule" className="btn btn-outline" style={{ textAlign: 'center', border: '1px dashed #cbd5e1' }}>
                                    <FaCalendarAlt /> {t('manufacturing.production_schedule', 'جدولة الإنتاج')}
                                </Link>
                            </div>
                        </div>

                        {/* Recent Orders */}
                        <div className="card">
                            <h3 className="section-title">{t('manufacturing.recent_orders') || 'أحدث أوامر التصنيع'}</h3>
                            {stats.orders.length === 0 ? (
                                <p className="text-muted mt-3 text-center py-8">{t('manufacturing.no_orders') || 'لا توجد أوامر تصنيع بعد'}</p>
                            ) : (
                                <div className="data-table-container mt-3">
                                    <table className="data-table">
                                        <thead>
                                            <tr>
                                                <th>{t('common.id')}</th>
                                                <th>{t('products.product')}</th>
                                                <th>{t('common.quantity')}</th>
                                                <th>{t('common.due_date')}</th>
                                                <th>{t('common.status')}</th>
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
            )}

            {/* Orders Tab Placeholder */}
            {activeTab === 'orders' && (
                <div className="card mt-4">
                    <div className="text-center py-8">
                        <p className="text-gray-500 mb-4">{t('manufacturing.orders_tab_desc') || 'عرض وإدارة جميع أوامر التصنيع'}</p>
                        <button className="btn btn-primary" onClick={() => navigate('/manufacturing/orders')}>
                            {t('manufacturing.go_to_orders') || 'الذهاب إلى صفحة الأوامر'} <FaArrowRight className="ml-2" />
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ManufacturingHome;
