import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { roleDashboardAPI } from '../../services/roleDashboard';
import { getUser } from '../../utils/auth';
import Card from '../../components/common/Card';
import {
    Crown, Calculator, TrendingUp, ShoppingCart, Warehouse, Users,
    Factory, FolderKanban, Monitor, Handshake, BarChart3, Compass,
} from 'lucide-react';

/**
 * KPIHub — landing page showing all available KPI dashboards.
 * صفحة مركز لوحات الأداء — تعرض جميع اللوحات المتاحة للمستخدم
 */

const ICON_MAP = {
    Crown, Calculator, TrendingUp, ShoppingCart, Warehouse, Users,
    Factory, FolderKanban, Monitor, Handshake, BarChart3, Compass,
};

const COLOR_MAP = {
    executive:     '#7c3aed',
    financial:     '#2563eb',
    sales:         '#059669',
    procurement:   '#d97706',
    warehouse:     '#0891b2',
    hr:            '#7c3aed',
    manufacturing: '#ea580c',
    projects:      '#4f46e5',
    pos:           '#0d9488',
    crm:           '#e11d48',
    industry:      '#8b5cf6',
};

const KPIHub = () => {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    const user = getUser();
    const isRTL = i18n.dir() === 'rtl';

    const [dashboards, setDashboards] = useState([]);
    const [defaultKey, setDefaultKey] = useState('executive');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetch = async () => {
            try {
                const res = await roleDashboardAPI.getAvailable();
                setDashboards(res.data?.dashboards || []);
                setDefaultKey(res.data?.default || 'executive');
            } catch (_) {}
            finally { setLoading(false); }
        };
        fetch();
    }, []);

    return (
        <div className="workspace fade-in">
            <div className="workspace-header" style={{ marginBottom: '1.5rem' }}>
                <h1 className="workspace-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <BarChart3 size={24} />
                    {t('kpi.kpi_dashboard_hub')}
                </h1>
                <p className="workspace-subtitle">
                    {t('kpi.select_dashboard_for_role')}
                </p>
            </div>

            {/* Quick access to auto-detected dashboard */}
            <div
                onClick={() => navigate('/kpi/auto')}
                className="card"
                style={{
                    display: 'flex', alignItems: 'center', gap: '1rem',
                    padding: '1.2rem 1.5rem', cursor: 'pointer',
                    background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                    border: 'none', color: '#fff', marginBottom: '1.5rem',
                    transition: 'transform .15s, box-shadow .15s',
                }}
                onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 8px 24px rgba(99,102,241,.3)'; }}
                onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.boxShadow = ''; }}
            >
                <Compass size={32} strokeWidth={1.5} />
                <div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>
                        {t('kpi.my_smart_dashboard')}
                    </div>
                    <div style={{ fontSize: '0.82rem', opacity: 0.85, marginTop: 2 }}>
                        {t('kpi.auto_dashboard_desc')}
                    </div>
                </div>
            </div>

            {/* Dashboard grid */}
            {loading ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem' }}>
                    {[1, 2, 3, 4, 5, 6].map(i => (
                        <div key={i} className="card animate-pulse" style={{ height: 140 }}>
                            <div style={{ height: 32, width: 32, borderRadius: 8, background: '#f1f5f9', marginBottom: 12 }} />
                            <div style={{ height: 14, background: '#f1f5f9', borderRadius: 6, width: '60%', marginBottom: 8 }} />
                            <div style={{ height: 10, background: '#f1f5f9', borderRadius: 6, width: '40%' }} />
                        </div>
                    ))}
                </div>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem' }}>
                    {dashboards.map(d => {
                        const IconComponent = ICON_MAP[d.icon] || BarChart3;
                        const color = COLOR_MAP[d.key] || '#6366f1';
                        const isDefault = d.key === defaultKey;

                        return (
                            <div
                                key={d.key}
                                onClick={() => navigate(`/kpi/${d.key}`)}
                                className="card"
                                style={{
                                    cursor: 'pointer',
                                    transition: 'all .2s',
                                    padding: '1.2rem',
                                    position: 'relative',
                                    borderColor: isDefault ? color + '44' : undefined,
                                }}
                                onMouseEnter={e => {
                                    e.currentTarget.style.boxShadow = `0 6px 20px ${color}22`;
                                    e.currentTarget.style.borderColor = color + '66';
                                    e.currentTarget.style.transform = 'translateY(-2px)';
                                }}
                                onMouseLeave={e => {
                                    e.currentTarget.style.boxShadow = '';
                                    e.currentTarget.style.borderColor = isDefault ? color + '44' : '';
                                    e.currentTarget.style.transform = '';
                                }}
                            >
                                {isDefault && (
                                    <span style={{
                                        position: 'absolute', top: 10, [isRTL ? 'left' : 'right']: 10,
                                        fontSize: '0.65rem', fontWeight: 700,
                                        background: color + '15', color: color,
                                        padding: '2px 8px', borderRadius: 20,
                                    }}>
                                        {t('kpi.default')}
                                    </span>
                                )}

                                <div style={{
                                    width: 40, height: 40, borderRadius: 10,
                                    background: color + '12', display: 'flex',
                                    alignItems: 'center', justifyContent: 'center',
                                    marginBottom: 12,
                                }}>
                                    <IconComponent size={22} style={{ color }} />
                                </div>

                                <div style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: 4 }}>
                                    {isRTL ? d.label_ar : d.label}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
};

export default KPIHub;
