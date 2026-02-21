import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { posAPI } from '../../utils/api';
import { useToast } from '../../context/ToastContext';
import { ChefHat, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import '../../components/ModuleStyles.css';

const KitchenDisplay = () => {
    const { t, i18n } = useTranslation();
    const { showToast } = useToast();
    const isRTL = i18n.language === 'ar';
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('pending');

    useEffect(() => { fetchOrders(); const interval = setInterval(fetchOrders, 15000); return () => clearInterval(interval); }, [filter]);

    const fetchOrders = async () => {
        try { setLoading(true); const res = await posAPI.listKitchenOrders({ status: filter !== 'all' ? filter : undefined }); setOrders(res.data || []); }
        catch (err) { console.error(err); } finally { setLoading(false); }
    };

    const updateStatus = async (id, status) => {
        try {
            await posAPI.updateKitchenOrderStatus(id, { status });
            showToast(t('pos.status_updated'), 'success');
            fetchOrders();
        } catch (err) { showToast('Error', 'error'); }
    };

    const statusConfig = {
        pending: { color: 'bg-yellow-100 text-yellow-700', icon: Clock, label: t('pos.status_pending') },
        preparing: { color: 'bg-blue-100 text-blue-700', icon: ChefHat, label: t('pos.status_preparing') },
        ready: { color: 'bg-green-100 text-green-700', icon: CheckCircle, label: t('pos.status_ready') },
        served: { color: 'bg-gray-100 text-gray-500', icon: CheckCircle, label: t('pos.status_served') },
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className="workspace-title"><span className="p-2 rounded-lg bg-red-50 text-red-600"><ChefHat size={24} /></span> {t('pos.kitchen_title')}</h1>
                        <p className="workspace-subtitle">{t('pos.kitchen_subtitle')}</p>
                    </div>
                </div>
            </div>

            {/* Filter Tabs */}
            <div className="d-flex gap-2 mb-4">
                {['all', 'pending', 'preparing', 'ready'].map(s => (
                    <button key={s} onClick={() => setFilter(s)} className={`btn ${filter === s ? 'btn-primary' : 'btn-secondary'}`}>
                        {s === 'all' ? (t('pos.filter_all')) : (statusConfig[s]?.label || s)}
                    </button>
                ))}
            </div>

            {/* Metrics */}
            <div className="metrics-grid mb-4">
                <div className="metric-card"><div className="metric-label">{t('pos.status_pending')}</div><div className="metric-value text-warning">{orders.filter(o => o.status === 'pending').length}</div></div>
                <div className="metric-card"><div className="metric-label">{t('pos.status_preparing')}</div><div className="metric-value text-primary">{orders.filter(o => o.status === 'preparing').length}</div></div>
                <div className="metric-card"><div className="metric-label">{t('pos.status_ready')}</div><div className="metric-value text-success">{orders.filter(o => o.status === 'ready').length}</div></div>
            </div>

            {/* Orders Grid */}
            {loading ? <div className="text-center p-8">...</div> : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {orders.map(order => {
                        const cfg = statusConfig[order.status] || statusConfig.pending;
                        const Icon = cfg.icon;
                        return (
                            <div key={order.id} className="card p-4" style={{ borderRight: isRTL ? `4px solid ${order.status === 'pending' ? '#d97706' : order.status === 'preparing' ? '#2563eb' : '#16a34a'}` : undefined, borderLeft: !isRTL ? `4px solid ${order.status === 'pending' ? '#d97706' : order.status === 'preparing' ? '#2563eb' : '#16a34a'}` : undefined }}>
                                <div className="d-flex justify-content-between align-items-center mb-3">
                                    <span className="font-bold text-lg">#{order.order_id || order.id}</span>
                                    <span className={`badge ${cfg.color}`}><Icon size={14} className="inline me-1" /> {cfg.label}</span>
                                </div>
                                {order.table_number && <div className="text-sm text-muted mb-2">{t('pos.table')} #{order.table_number}</div>}
                                <div className="mb-3">
                                    {(order.items || []).map((item, idx) => (
                                        <div key={idx} className="d-flex justify-content-between py-1 border-bottom">
                                            <span>{item.product_name || item.name}</span>
                                            <span className="font-bold">×{item.quantity}</span>
                                        </div>
                                    ))}
                                    {order.notes && <div className="mt-2 p-2 bg-yellow-50 rounded text-sm"><AlertCircle size={14} className="inline me-1" /> {order.notes}</div>}
                                </div>
                                <div className="d-flex gap-2">
                                    {order.status === 'pending' && <button className="btn btn-sm btn-primary flex-1" onClick={() => updateStatus(order.id, 'preparing')}>{t('pos.start_preparing')}</button>}
                                    {order.status === 'preparing' && <button className="btn btn-sm btn-success flex-1" onClick={() => updateStatus(order.id, 'ready')}>{t('pos.status_ready')}</button>}
                                    {order.status === 'ready' && <button className="btn btn-sm btn-secondary flex-1" onClick={() => updateStatus(order.id, 'served')}>{t('pos.status_served')}</button>}
                                </div>
                            </div>
                        );
                    })}
                    {orders.length === 0 && <div className="col-span-3 text-center p-8 text-muted">{t('pos.no_orders')}</div>}
                </div>
            )}
        </div>
    );
};

export default KitchenDisplay;
