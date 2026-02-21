import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import api from '../../utils/api';
import { Factory, Play, CheckCircle, Clock, Plus, ArrowRight, Package } from 'lucide-react';
import { useToast } from '../../context/ToastContext';
import { useBranch } from '../../context/BranchContext';
import '../../components/ModuleStyles.css';

const ProductionOrderList = () => {
    const { t, i18n } = useTranslation();
    const { currentBranch, loading: branchLoading } = useBranch();
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const navigate = useNavigate();
    const { showToast } = useToast();
    const isRTL = i18n.dir() === 'rtl';

    useEffect(() => {
        if (!branchLoading) {
            fetchOrders();
        }
    }, [currentBranch, branchLoading]);

    const fetchOrders = async () => {
        try {
            const params = {};
            if (currentBranch) params.branch_id = currentBranch.id;
            const res = await api.get('/manufacturing/orders', { params });
            setOrders(res.data);
            setError(null);
        } catch (err) {
            console.error(err);
            setError(t('common.error_loading_data'));
        } finally {
            setLoading(false);
        }
    };

    const getStatusBadge = (status) => {
        switch (status) {
            case 'completed': return 'badge-success';
            case 'in_progress': return 'badge-warning';
            case 'draft': return 'badge';
            case 'cancelled': return 'badge-danger';
            default: return 'badge';
        }
    };

    const handleFinish = async (id) => {
        if (!window.confirm(t('manufacturing.confirm_complete'))) return;
        try {
            await api.post(`/manufacturing/orders/${id}/complete`);
            showToast(t('manufacturing.order_completed'), 'success');
            fetchOrders();
        } catch (err) {
            console.error("Failed to complete order", err);
            showToast(t('common.error_occurred'), 'error');
        }
    };

    if (loading) {
        return (
            <div className="workspace flex items-center justify-center fade-in">
                <div className="text-center">
                    <span className="loading"></span>
                    <p className="text-slate-500">{t('common.loading')}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className="workspace-title flex items-center gap-2">
                            <span className="p-2 rounded-lg bg-amber-50 text-amber-600">
                                <Factory size={24} />
                            </span>
                            {t('manufacturing.production_orders')}
                        </h1>
                        <p className="workspace-subtitle">
                            {t('manufacturing.production_orders_desc') || 'إدارة أوامر التصنيع والإنتاج'}
                        </p>
                    </div>
                    <button
                        className="btn btn-primary gap-2"
                        onClick={() => navigate('/manufacturing/orders/new')}
                    >
                        <Plus size={18} />
                        {t('manufacturing.new_order')}
                    </button>
                </div>
            </div>

            {error && (
                <div className="alert alert-error mb-4">
                    <span>{error}</span>
                </div>
            )}

            <div className="card bg-base-100 shadow-sm">
                <div className="card-body p-0">
                    {orders.length === 0 ? (
                        <div className="text-center py-16">
                            <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Package size={40} className="text-slate-400" />
                            </div>
                            <h3 className="text-lg font-semibold text-slate-600 mb-2">
                                {t('manufacturing.no_orders')}
                            </h3>
                            <p className="text-slate-500 mb-4">
                                {t('manufacturing.no_orders_desc') || 'لم يتم إنشاء أي أوامر تصنيع بعد'}
                            </p>
                            <button
                                className="btn btn-primary gap-2"
                                onClick={() => navigate('/manufacturing/orders/new')}
                            >
                                <Plus size={18} />
                                {t('manufacturing.new_order')}
                            </button>
                        </div>
                    ) : (
                        <div className="data-table-container">
                            <table className="data-table">
                                <thead className="bg-slate-50">
                                    <tr>
                                        <th>#</th>
                                        <th>{t('manufacturing.bom')}</th>
                                        <th>{t('manufacturing.quantity')}</th>
                                        <th>{t('common.start_date')}</th>
                                        <th>{t('common.status')}</th>
                                        <th>{t('common.actions')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {orders.map((order) => (
                                        <tr key={order.id} className="hover">
                                            <th className="font-mono text-slate-500">{order.id}</th>
                                            <td>
                                                <div className="font-bold">{order.bom_name}</div>
                                            </td>
                                            <td>
                                                <span style={{ background: 'var(--bg-secondary)', borderRadius: '6px', padding: '2px 8px', fontSize: '12px', fontWeight: 600 }}>{order.quantity}</span>
                                            </td>
                                            <td className="text-slate-600">
                                                {order.start_date ? new Date(order.start_date).toLocaleDateString() : '-'}
                                            </td>
                                            <td>
                                                <div className={`badge ${getStatusBadge(order.status)} gap-1`}>
                                                    {order.status === 'in_progress' && <Clock size={12} />}
                                                    {order.status === 'completed' && <CheckCircle size={12} />}
                                                    {t(`manufacturing.status.${order.status}`, order.status)}
                                                </div>
                                            </td>
                                            <td>
                                                {order.status !== 'completed' && order.status !== 'cancelled' && (
                                                    <button
                                                        className="btn btn-sm btn-success text-white gap-1"
                                                        onClick={() => handleFinish(order.id)}
                                                    >
                                                        <CheckCircle size={14} />
                                                        {t('manufacturing.finish')}
                                                    </button>
                                                )}
                                            </td>
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

export default ProductionOrderList;
