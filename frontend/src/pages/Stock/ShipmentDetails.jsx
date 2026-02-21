import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { inventoryAPI } from '../../utils/api';

import { formatShortDate, formatDateTime } from '../../utils/dateUtils';

const ShipmentDetails = () => {
    const { t, i18n } = useTranslation();
    const { id } = useParams();
    const navigate = useNavigate();
    const [shipment, setShipment] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDetails();
    }, [id]);

    const fetchDetails = async () => {
        try {
            const res = await inventoryAPI.getShipmentDetails(id);
            setShipment(res.data);
        } catch (err) {
            console.error("Failed to load shipment", err);
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
                padding: '6px 16px',
                borderRadius: '16px',
                fontSize: '14px',
                fontWeight: '600'
            }}>
                {s.label}
            </span>
        );
    };

    if (loading) return <div className="p-8 text-center">{t('common.loading')}</div>;
    if (!shipment) return <div className="p-8 text-center text-danger">{t('stock.shipments.not_found')}</div>;

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div className="header-title">
                    <h1 className="workspace-title">🚚 {t('stock.shipments.view')} {shipment.shipment_ref}</h1>
                    <p className="workspace-subtitle">{t('stock.shipments.subtitle')}</p>
                </div>
                <div className="header-actions">
                    {getStatusBadge(shipment.status)}
                    <button className="btn btn-secondary" onClick={() => navigate('/stock/shipments')}>
                        {t('common.back')}
                    </button>
                </div>
            </div>

            {/* Info Cards */}
            <div className="metrics-grid" style={{ marginBottom: '24px' }}>
                <div className="metric-card">
                    <div className="metric-label">{t('stock.shipments.form.from_warehouse')}</div>
                    <div className="metric-value" style={{ fontSize: '18px' }}>📍 {shipment.source_warehouse}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('stock.shipments.form.to_warehouse')}</div>
                    <div className="metric-value" style={{ fontSize: '18px' }}>🎯 {shipment.destination_warehouse}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('stock.shipments.table.date')}</div>
                    <div className="metric-value" style={{ fontSize: '16px' }}>
                        {formatShortDate(shipment.created_at)}
                    </div>
                </div>
                {shipment.received_at && (
                    <div className="metric-card" style={{ borderRight: '4px solid #059669' }}>
                        <div className="metric-label">{t('stock.shipments.status.received')}</div>
                        <div className="metric-value" style={{ fontSize: '16px', color: '#059669' }}>
                            {formatShortDate(shipment.received_at)}
                        </div>
                    </div>
                )}
            </div>

            {/* Items */}
            <div className="section-card">
                <h3 className="section-title">📦 {t('stock.shipments.form.shipped_products')}</h3>
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>{t('stock.details.table.product_code')}</th>
                            <th>{t('stock.details.table.product_name')}</th>
                            <th>{t('stock.shipments.form.quantity')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {(shipment.items || []).map((item, idx) => (
                            <tr key={idx}>
                                <td className="text-muted">{item.product_code}</td>
                                <td className="font-medium">{item.product_name}</td>
                                <td className="font-bold">{item.quantity}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Notes */}
            {shipment.notes && (
                <div className="section-card" style={{ marginTop: '20px' }}>
                    <h3 className="section-title">📝 {t('stock.shipments.form.notes')}</h3>
                    <p>{shipment.notes}</p>
                </div>
            )}

            {/* Footer */}
            <div style={{ marginTop: '20px', display: 'flex', gap: '16px', fontSize: '13px', color: 'var(--text-muted)' }}>
                <span>{t('stock.shipments.incoming_page.by_user', { user: shipment.created_by_name })}</span>
                {shipment.received_by_name && <span>• {t('stock.shipments.status.received')} {t('common.by')}: {shipment.received_by_name}</span>}
            </div>
        </div>
    );
};

export default ShipmentDetails;
