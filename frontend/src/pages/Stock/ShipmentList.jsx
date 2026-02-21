import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { inventoryAPI } from '../../utils/api';
import { useBranch } from '../../context/BranchContext';

const ShipmentList = () => {
    const { t } = useTranslation();
    const { currentBranch } = useBranch();
    const [shipments, setShipments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('');

    useEffect(() => {
        fetchShipments();
    }, [filter, currentBranch]);

    const fetchShipments = async () => {
        try {
            const res = await inventoryAPI.listShipments({ status_filter: filter || undefined, branch_id: currentBranch?.id });
            setShipments(res.data);
        } catch (err) {
            console.error("Failed to load shipments", err);
        } finally {
            setLoading(false);
        }
    };

    const getStatusBadge = (status) => {
        const styles = {
            pending: { bg: '#FEF3C7', color: '#D97706', label: t('stock.shipments.status.pending') },
            received: { bg: '#D1FAE5', color: '#059669', label: t('stock.shipments.status.received') },
            cancelled: { bg: '#FEE2E2', color: '#DC2626', label: t('stock.shipments.status.cancelled') }
        };
        const s = styles[status] || styles.pending;
        return (
            <span style={{
                background: s.bg,
                color: s.color,
                padding: '4px 12px',
                borderRadius: '12px',
                fontSize: '12px',
                fontWeight: '600'
            }}>
                {s.label}
            </span>
        );
    };

    if (loading) return <div className="p-8 text-center">{t('common.loading')}</div>;

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div className="header-title">
                    <h1 className="workspace-title">📦 {t('stock.shipments.title')}</h1>
                    <p className="workspace-subtitle">{t('stock.shipments.subtitle')}</p>
                </div>
                <div className="header-actions">
                    <Link to="/stock/shipments/incoming" className="btn btn-secondary">
                        📥 {t('stock.shipments.incoming')}
                    </Link>
                    <Link to="/stock/shipments/new" className="btn btn-primary">
                        + {t('stock.shipments.new_shipment')}
                    </Link>
                </div>
            </div>

            {/* Filters */}
            <div className="section-card" style={{ marginBottom: '24px' }}>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                    <span style={{ fontWeight: '600' }}>{t('stock.shipments.filter_status')}</span>
                    <select
                        className="form-input"
                        style={{ width: 'auto' }}
                        value={filter}
                        onChange={e => setFilter(e.target.value)}
                    >
                        <option value="">{t('stock.shipments.all')}</option>
                        <option value="pending">{t('stock.shipments.status.pending')}</option>
                        <option value="received">{t('stock.shipments.status.received')}</option>
                        <option value="cancelled">{t('stock.shipments.status.cancelled')}</option>
                    </select>
                </div>
            </div>

            {/* Table */}
            <div className="section-card">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>{t('stock.shipments.table.ref')}</th>
                            <th>{t('stock.shipments.table.from')}</th>
                            <th>{t('stock.shipments.table.to')}</th>
                            <th>{t('stock.shipments.table.items')}</th>
                            <th>{t('stock.shipments.table.status')}</th>
                            <th>{t('stock.shipments.table.date')}</th>
                            <th>{t('stock.shipments.table.actions')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {shipments.length === 0 && (
                            <tr>
                                <td colSpan="7" className="text-center text-muted py-5">
                                    {t('stock.shipments.empty')}
                                </td>
                            </tr>
                        ) || null}
                        {shipments.map(s => (
                            <tr key={s.id}>
                                <td className="font-medium">{s.shipment_ref}</td>
                                <td>{s.source_warehouse}</td>
                                <td>{s.destination_warehouse}</td>
                                <td>{s.item_count}</td>
                                <td>{getStatusBadge(s.status)}</td>
                                <td className="text-muted">
                                    {new Date(s.created_at).toLocaleDateString('ar-SA')}
                                </td>
                                <td>
                                    <Link to={`/stock/shipments/${s.id}`} className="btn btn-sm btn-secondary">
                                        {t('stock.shipments.view')}
                                    </Link>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default ShipmentList;
