import React from 'react';
import { useTranslation } from 'react-i18next';
import { AlertTriangle, AlertCircle, Info, CheckCircle, XCircle } from 'lucide-react';

/**
 * AlertBanner — displays alerts with severity level from the KPI engine.
 * شريط التنبيهات حسب الخطورة
 *
 * Props:
 *   alerts — [{ level: critical|warning|info|success, message, message_ar, action_url?, action_label? }]
 */

const LEVEL_STYLES = {
    critical: { bg: '#fef2f2', border: '#fca5a5', text: '#991b1b', icon: XCircle,       dot: '#ef4444' },
    warning:  { bg: '#fffbeb', border: '#fde68a', text: '#92400e', icon: AlertTriangle,  dot: '#f59e0b' },
    info:     { bg: '#eff6ff', border: '#bfdbfe', text: '#1e40af', icon: Info,           dot: '#3b82f6' },
    success:  { bg: '#f0fdf4', border: '#bbf7d0', text: '#166534', icon: CheckCircle,    dot: '#22c55e' },
};

const AlertBanner = ({ alerts = [] }) => {
    const { i18n } = useTranslation();
    const isRTL = i18n.dir() === 'rtl';

    if (!alerts || alerts.length === 0) return null;

    // Sort: critical first
    const sorted = [...alerts].sort((a, b) => {
        const order = { critical: 0, warning: 1, info: 2, success: 3 };
        return (order[a.level] ?? 9) - (order[b.level] ?? 9);
    });

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {sorted.map((alert, idx) => {
                const style = LEVEL_STYLES[alert.level] || LEVEL_STYLES.info;
                const Icon = style.icon;
                const message = isRTL ? (alert.message_ar || alert.message) : (alert.message || alert.message_ar);

                return (
                    <div key={idx} style={{
                        display: 'flex', alignItems: 'center', gap: '10px',
                        padding: '10px 14px',
                        background: style.bg,
                        border: `1px solid ${style.border}`,
                        borderRadius: '8px',
                        direction: isRTL ? 'rtl' : 'ltr',
                    }}>
                        <Icon size={16} style={{ color: style.dot, flexShrink: 0 }} />
                        <span style={{ fontSize: '0.82rem', fontWeight: 500, color: style.text, flex: 1 }}>
                            {message}
                        </span>
                        {alert.action_url && (
                            <a
                                href={alert.action_url}
                                style={{
                                    fontSize: '0.75rem', fontWeight: 600,
                                    color: style.dot, textDecoration: 'none',
                                    whiteSpace: 'nowrap',
                                }}
                            >
                                {alert.action_label || (isRTL ? 'عرض' : 'View')} →
                            </a>
                        )}
                    </div>
                );
            })}
        </div>
    );
};

export default AlertBanner;
