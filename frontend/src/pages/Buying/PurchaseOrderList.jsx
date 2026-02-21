import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { purchasesAPI } from '../../utils/api';
import { getCurrency, hasPermission } from '../../utils/auth';
import { useBranch } from '../../context/BranchContext';
import { useTranslation } from 'react-i18next';
import { formatNumber } from '../../utils/format';
import '../../components/ModuleStyles.css';
import { toastEmitter } from '../../utils/toastEmitter';

function PurchaseOrderList() {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [approving, setApproving] = useState(null);
    const currency = getCurrency();
    const { currentBranch } = useBranch();

    useEffect(() => {
        fetchOrders();
    }, [currentBranch]);

    const fetchOrders = async () => {
        try {
            setLoading(true);
            const params = {};
            if (currentBranch?.id) params.branch_id = currentBranch.id;
            const response = await purchasesAPI.listOrders(params);
            setOrders(response.data);
        } catch (err) {
            console.error("Failed to fetch purchase orders", err);
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async (id) => {
        if (!window.confirm(t('buying.orders.confirm_approve'))) return;
        try {
            setApproving(id);
            await purchasesAPI.approveOrder(id);
            fetchOrders();
        } catch (err) {
            toastEmitter.emit(err.response?.data?.detail || t('common.error'), 'error');
        } finally {
            setApproving(null);
        }
    };

    const getStatusBadge = (status) => {
        const styles = {
            draft: { bg: '#f3f4f6', color: '#374151', label: t('buying.orders.status.draft') },
            approved: { bg: '#dbeafe', color: '#1d4ed8', label: t('buying.orders.status.approved') },
            partial: { bg: '#fef3c7', color: '#d97706', label: t('buying.orders.status.partial') },
            received: { bg: '#d1fae5', color: '#059669', label: t('buying.orders.status.received') },
            cancelled: { bg: '#fee2e2', color: '#dc2626', label: t('buying.orders.status.cancelled') }
        };
        const style = styles[status] || styles.draft;
        return (
            <span style={{
                backgroundColor: style.bg,
                color: style.color,
                padding: '4px 12px',
                borderRadius: '12px',
                fontSize: '12px',
                fontWeight: '500'
            }}>
                {style.label}
            </span>
        );
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div>
                    <h1 className="workspace-title">📋 {t('buying.orders.title')}</h1>
                    <p className="workspace-subtitle">{t('buying.orders.subtitle')}</p>
                </div>
                <div className="header-actions">
                    {hasPermission('buying.create') && (
                        <button
                            className="btn btn-primary"
                            onClick={() => navigate('/buying/orders/new')}
                        >
                            + {t('buying.orders.create')}
                        </button>
                    )}
                </div>
            </div>

            <div className="card">
                {loading ? (
                    <div className="p-8 text-center">{t('common.loading')}...</div>
                ) : orders.length === 0 ? (
                    <div className="p-8 text-center" style={{ color: 'var(--text-muted)' }}>
                        {t('buying.orders.empty')}
                    </div>
                ) : (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>{t('buying.orders.table.number')}</th>
                                <th>{t('buying.orders.table.supplier')}</th>
                                <th>{t('buying.orders.table.date')}</th>
                                <th>{t('buying.orders.table.total')}</th>
                                <th>{t('buying.orders.table.status')}</th>
                                <th>{t('common.actions')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {orders.map(order => (
                                <tr key={order.id}>
                                    <td>
                                        <span
                                            style={{ color: 'var(--primary)', cursor: 'pointer', fontWeight: '500' }}
                                            onClick={() => navigate(`/buying/orders/${order.id}`)}
                                        >
                                            {order.po_number}
                                        </span>
                                    </td>
                                    <td>{order.supplier_name}</td>
                                    <td>{new Date(order.order_date).toLocaleDateString('ar-EG')}</td>
                                    <td style={{ fontWeight: '500' }}>
                                        {formatNumber(order.total)} <small>{currency}</small>
                                    </td>
                                    <td>{getStatusBadge(order.status)}</td>
                                    <td>
                                        <div style={{ display: 'flex', gap: '8px' }}>
                                            <button
                                                className="btn btn-sm btn-secondary"
                                                onClick={() => navigate(`/buying/orders/${order.id}`)}
                                            >
                                                {t('common.view')}
                                            </button>
                                            {order.status === 'draft' && hasPermission('buying.approve') && (
                                                <button
                                                    className="btn btn-sm btn-success"
                                                    onClick={() => handleApprove(order.id)}
                                                    disabled={approving === order.id}
                                                >
                                                    {approving === order.id ? '...' : t('buying.orders.approve')}
                                                </button>
                                            )}
                                            {(order.status === 'approved' || order.status === 'partial') && hasPermission('buying.receive') && (
                                                <button
                                                    className="btn btn-sm btn-primary"
                                                    onClick={() => navigate(`/buying/orders/${order.id}/receive`)}
                                                >
                                                    {t('buying.orders.receive')}
                                                </button>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
}

export default PurchaseOrderList;
