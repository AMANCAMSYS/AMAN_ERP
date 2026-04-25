import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import { Boxes, Package, ArrowRight, Search } from 'lucide-react';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';
import { PageLoading } from '../../components/common/LoadingStates'

export default function MRPPlanning() {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchOrders();
    }, []);

    const fetchOrders = async () => {
        try {
            setLoading(true);
            const res = await api.get('/manufacturing/orders');
            // Filter only non-completed and non-cancelled orders for planning
            const activeOrders = res.data.filter(o => o.status !== 'completed' && o.status !== 'cancelled');
            setOrders(activeOrders);
        } catch (err) {
            toastEmitter.emit(t('common.error'), 'error');
        } finally {
            setLoading(false);
        }
    };

    const filteredOrders = orders.filter(o =>
        o.order_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
        o.product_name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) {
        return (
            <div className="workspace flex items-center justify-center pt-5">
                <PageLoading />
            </div>
        );
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div>
                    <h1 className="workspace-title flex items-center gap-2">
                        <Boxes size={24} className="text-primary" />
                        {t('manufacturing.mrp.title')}
                    </h1>
                    <p className="workspace-subtitle">
                        {t('manufacturing.mrp.planning_desc')}
                    </p>
                </div>
            </div>

            <div style={{ maxWidth: '480px', marginBottom: '24px' }}>
                <div className="search-box" style={{ width: '100%' }}>
                    <Search size={16} />
                    <input
                        type="text"
                        placeholder={t('common.search')}
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            <div className="data-table-container">
                <table className="data-table">
                        <thead>
                            <tr>
                                <th>{t('common.id')}</th>
                                <th>{t('products.product')}</th>
                                <th>{t('manufacturing.bom')}</th>
                                <th className="text-center">{t('common.quantity')}</th>
                                <th className="text-center">{t('common.status_title')}</th>
                                <th className="text-center">{t('common.actions')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredOrders.length === 0 ? (
                                <tr>
                                    <td colSpan="6" className="text-center py-5 text-muted">
                                        <Package size={48} className="mb-3 opacity-20" />
                                        <p>{t('manufacturing.mrp.no_active_orders')}</p>
                                    </td>
                                </tr>
                            ) : (
                                filteredOrders.map(order => (
                                    <tr key={order.id}>
                                        <td className="font-mono fw-bold text-primary">{order.order_number}</td>
                                        <td>{order.product_name}</td>
                                        <td>{order.bom_name}</td>
                                        <td className="text-center fw-bold">{order.quantity}</td>
                                        <td className="text-center">
                                            <span className={`badge ${order.status === 'in_progress' ? 'badge-warning' : 'badge-info'}`}>
                                                {t(`manufacturing.status.${order.status}`, order.status)}
                                            </span>
                                        </td>
                                        <td className="text-center">
                                            <button
                                                className="btn btn-primary btn-sm d-inline-flex align-items-center gap-1"
                                                onClick={() => navigate(`/manufacturing/mrp/${order.id}`)}
                                            >
                                                {t('manufacturing.check_availability')}
                                                <ArrowRight size={14} />
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
            </div>
        </div>
    );
}
