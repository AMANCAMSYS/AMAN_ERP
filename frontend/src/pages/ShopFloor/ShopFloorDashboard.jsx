import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { shopFloorAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import { Activity, Eye, AlertTriangle } from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';

const ShopFloorDashboard = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const navigate = useNavigate();
    const [workOrders, setWorkOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [toasts, setToasts] = useState([]);
    const wsRef = useRef(null);

    const loadDashboard = useCallback(() => {
        shopFloorAPI.getDashboard()
            .then(res => setWorkOrders(res.data || []))
            .catch(() => toastEmitter.emit(t('common.error'), 'error'))
            .finally(() => setLoading(false));
    }, []);

    useEffect(() => {
        loadDashboard();
    }, [loadDashboard]);

    // WebSocket for live updates
    useEffect(() => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/manufacturing/shopfloor/ws`;
        let ws;
        try {
            ws = new WebSocket(wsUrl);
            ws.onmessage = (evt) => {
                try {
                    const msg = JSON.parse(evt.data);
                    // Show toast for delay alerts
                    if (msg.is_delayed) {
                        const toast = {
                            id: Date.now(),
                            text: `${t('shopfloor.delay_alert')}: WO #${msg.work_order_id}`,
                            type: 'warning',
                        };
                        setToasts(prev => [...prev, toast]);
                        setTimeout(() => setToasts(prev => prev.filter(tt => tt.id !== toast.id)), 8000);
                    }
                    // Refresh dashboard on any event
                    loadDashboard();
                } catch { /* ignore parse errors */ }
            };
            ws.onerror = () => {};
            ws.onclose = () => {};
            wsRef.current = ws;
        } catch { /* WebSocket not available */ }

        return () => {
            if (ws && ws.readyState === WebSocket.OPEN) ws.close();
        };
    }, [loadDashboard, t]);

    const getProgressColor = (pct, delayed) => {
        if (delayed) return '#ef4444';
        if (pct >= 80) return '#22c55e';
        if (pct >= 40) return '#f59e0b';
        return '#3b82f6';
    };

    const statusBadge = (status) => {
        const colors = {
            in_progress: '#3b82f6',
            completed: '#22c55e',
            paused: '#f59e0b',
            released: '#8b5cf6',
            started: '#3b82f6',
        };
        return (
            <span style={{
                padding: '2px 8px', borderRadius: 12,
                background: `${colors[status] || '#6b7280'}20`,
                color: colors[status] || '#6b7280',
                fontSize: 12, fontWeight: 600,
            }}>
                {t(`shopfloor.status_${status}`) || status}
            </span>
        );
    };

    return (
        <div className="module-container" dir={isRTL ? 'rtl' : 'ltr'}>
            <BackButton />
            <div className="module-header">
                <h1><Activity size={24} /> {t('shopfloor.dashboard')}</h1>
                <button className="btn btn-outline" onClick={loadDashboard}>
                    {t('common.refresh')}
                </button>
            </div>

            {/* Toast notifications */}
            <div style={{ position: 'fixed', top: 16, right: 16, zIndex: 9999, display: 'flex', flexDirection: 'column', gap: 8 }}>
                {toasts.map(toast => (
                    <div key={toast.id} style={{
                        background: toast.type === 'warning' ? '#fef3c7' : '#dbeafe',
                        border: `1px solid ${toast.type === 'warning' ? '#f59e0b' : '#3b82f6'}`,
                        padding: '12px 16px', borderRadius: 8, minWidth: 280,
                        display: 'flex', alignItems: 'center', gap: 8,
                    }}>
                        <AlertTriangle size={16} color="#f59e0b" />
                        {toast.text}
                    </div>
                ))}
            </div>

            {/* KPIs */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16, marginBottom: 24 }}>
                <div className="stat-card">
                    <div className="stat-value">{workOrders.length}</div>
                    <div className="stat-label">{t('shopfloor.active_orders')}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value" style={{ color: '#ef4444' }}>
                        {workOrders.filter(w => w.is_delayed).length}
                    </div>
                    <div className="stat-label">{t('shopfloor.delayed_orders')}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">
                        {workOrders.filter(w => w.current_operation_status === 'in_progress').length}
                    </div>
                    <div className="stat-label">{t('shopfloor.in_progress')}</div>
                </div>
            </div>

            {loading ? (
                <div className="loading-spinner">{t('common.loading')}</div>
            ) : workOrders.length === 0 ? (
                <div className="empty-state">{t('shopfloor.no_active_orders')}</div>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 16 }}>
                    {workOrders.map(wo => (
                        <div key={wo.work_order_id} className="form-card" style={{
                            borderLeft: `4px solid ${getProgressColor(wo.progress_pct, wo.is_delayed)}`,
                            cursor: 'pointer',
                        }}
                            onClick={() => navigate(`/manufacturing/shopfloor/work-order/${wo.work_order_id}`)}
                        >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                                <strong>{wo.order_number || `WO #${wo.work_order_id}`}</strong>
                                {statusBadge(wo.status)}
                            </div>
                            <div style={{ fontSize: 13, color: '#6b7280', marginBottom: 8 }}>
                                {wo.product_name} — {t('shopfloor.qty')}: {wo.quantity}
                            </div>
                            {wo.current_operation && (
                                <div style={{ fontSize: 12, marginBottom: 8 }}>
                                    {t('shopfloor.current_op')}: <strong>{wo.current_operation}</strong>
                                </div>
                            )}
                            {/* Progress bar */}
                            <div style={{ background: '#e5e7eb', borderRadius: 8, height: 10, overflow: 'hidden' }}>
                                <div style={{
                                    width: `${wo.progress_pct}%`,
                                    height: '100%',
                                    background: getProgressColor(wo.progress_pct, wo.is_delayed),
                                    borderRadius: 8,
                                    transition: 'width 0.5s',
                                }} />
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginTop: 4, color: '#9ca3af' }}>
                                <span>{wo.progress_pct}%</span>
                                {wo.due_date && <span>{t('shopfloor.due')}: {wo.due_date}</span>}
                            </div>
                            {wo.is_delayed && (
                                <div style={{ color: '#ef4444', fontSize: 12, marginTop: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                                    <AlertTriangle size={14} /> {t('shopfloor.delayed')}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default ShopFloorDashboard;
