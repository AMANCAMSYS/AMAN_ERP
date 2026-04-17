import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { securityAPI } from '../../services/security';
import { useToast } from '../../context/ToastContext';
import { Shield, AlertTriangle, Eye, Lock, RefreshCw, Activity } from 'lucide-react';
import BackButton from '../../components/common/BackButton';
import '../../components/ModuleStyles.css';

const SecurityEvents = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const { showToast } = useToast();
    const [activeTab, setActiveTab] = useState('events');
    const [events, setEvents] = useState([]);
    const [summary, setSummary] = useState({});
    const [loginAttempts, setLoginAttempts] = useState([]);
    const [blockedIPs, setBlockedIPs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState({ event_type: '', severity: '' });
    const [page, setPage] = useState(1);
    const [totalEvents, setTotalEvents] = useState(0);
    const PAGE_SIZE = 25;

    useEffect(() => { fetchData(); }, [activeTab, filter, page]);

    const fetchData = async () => {
        try {
            setLoading(true);
            if (activeTab === 'events') {
                const [evRes, sumRes] = await Promise.all([
                    securityAPI.listSecurityEvents({ ...filter, page, limit: PAGE_SIZE }),
                    securityAPI.getSecurityEventsSummary()
                ]);
                const evData = evRes.data;
                if (Array.isArray(evData)) {
                    setEvents(evData);
                    setTotalEvents(evData.length >= PAGE_SIZE ? (page * PAGE_SIZE) + 1 : ((page - 1) * PAGE_SIZE) + evData.length);
                } else {
                    setEvents(evData?.items || evData?.data || []);
                    setTotalEvents(evData?.total || evData?.count || 0);
                }
                setSummary(sumRes.data || {});
            } else if (activeTab === 'attempts') {
                const res = await securityAPI.listLoginAttempts({});
                setLoginAttempts(res.data || []);
            } else {
                const res = await securityAPI.getBlockedIPs();
                setBlockedIPs(res.data || []);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const severityColor = (sev) => {
        const map = { critical: '#dc3545', high: '#fd7e14', medium: '#ffc107', low: '#28a745', info: '#17a2b8' };
        return map[sev] || '#6c757d';
    };

    const formatDate = (d) => d ? new Date(d).toLocaleString(isRTL ? 'ar-SA' : 'en-US') : '—';

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="d-flex align-items-center justify-content-between w-100">
                    <div>
                        <h1 className="workspace-title">
                            <Shield size={24} className="me-2" />
                            {t('security_events.title')}
                        </h1>
                        <p className="workspace-subtitle">
                            {t('security_events.subtitle')}
                        </p>
                    </div>
                    <button className="btn btn-outline-primary" onClick={fetchData}>
                        <RefreshCw size={16} className="me-1" /> {t('security_events.refresh')}
                    </button>
                </div>
            </div>

            {/* Summary Metrics */}
            <div className="metrics-grid mb-4">
                <div className="metric-card">
                    <div className="metric-icon" style={{ background: '#e3f2fd' }}><Activity size={22} color="#1976d2" /></div>
                    <div className="metric-info">
                        <span className="metric-value">{summary.total_events || 0}</span>
                        <span className="metric-label">{t('security_events.total_events')}</span>
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-icon" style={{ background: '#fff3e0' }}><AlertTriangle size={22} color="#ef6c00" /></div>
                    <div className="metric-info">
                        <span className="metric-value">{summary.last_24h || 0}</span>
                        <span className="metric-label">{t('security_events.last_24h')}</span>
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-icon" style={{ background: '#fce4ec' }}><Lock size={22} color="#c62828" /></div>
                    <div className="metric-info">
                        <span className="metric-value">{blockedIPs.length || 0}</span>
                        <span className="metric-label">{t('security_events.blocked_ips')}</span>
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div className="tabs mb-3">
                {[
                    { key: 'events', label: t('security_events.tab_events'), icon: <Eye size={16} /> },
                    { key: 'attempts', label: t('security_events.tab_attempts'), icon: <Lock size={16} /> },
                    { key: 'blocked', label: t('security_events.tab_blocked'), icon: <AlertTriangle size={16} /> },
                ].map(tab => (
                    <button key={tab.key}
                        className={`tab ${activeTab === tab.key ? 'active' : ''}`}
                        onClick={() => setActiveTab(tab.key)}>
                        {tab.icon} <span className="ms-1">{tab.label}</span>
                    </button>
                ))}
            </div>

            {/* Filters for events tab */}
            {activeTab === 'events' && (
                <div className="d-flex gap-2 mb-3">
                    <select className="form-input" style={{ maxWidth: 200 }}
                        value={filter.severity} onChange={e => { setPage(1); setFilter(p => ({ ...p, severity: e.target.value })); }}>
                        <option value="">{t('security_events.all_severities')}</option>
                        {['critical', 'high', 'medium', 'low', 'info'].map(s => (
                            <option key={s} value={s}>{s}</option>
                        ))}
                    </select>
                    <select className="form-input" style={{ maxWidth: 200 }}
                        value={filter.event_type} onChange={e => { setPage(1); setFilter(p => ({ ...p, event_type: e.target.value })); }}>
                        <option value="">{t('security_events.all_types')}</option>
                        {(summary.by_type || []).map(t => (
                            <option key={t.event_type} value={t.event_type}>{t.event_type} ({t.cnt})</option>
                        ))}
                    </select>
                </div>
            )}

            <div className="section-card">
                {loading ? (
                    <div className="text-center p-5"><div className="spinner-border" /></div>
                ) : activeTab === 'events' ? (
                    <div className="data-table-container">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>{t('security_events.date')}</th>
                                    <th>{t('security_events.type')}</th>
                                    <th>{t('security_events.severity')}</th>
                                    <th>{t('security_events.ip_address')}</th>
                                    <th>{t('security_events.details')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {events.length === 0 ? (
                                    <tr><td colSpan={5} className="text-center p-4">{t('security_events.no_events')}</td></tr>
                                ) : events.map(ev => (
                                    <tr key={ev.id}>
                                        <td style={{ whiteSpace: 'nowrap' }}>{formatDate(ev.created_at)}</td>
                                        <td><span className="badge bg-secondary">{ev.event_type}</span></td>
                                        <td>
                                            <span className="badge" style={{ background: severityColor(ev.severity), color: '#fff' }}>
                                                {ev.severity}
                                            </span>
                                        </td>
                                        <td><code>{ev.ip_address || '—'}</code></td>
                                        <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                            {typeof ev.details === 'object' ? JSON.stringify(ev.details) : ev.details || '—'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        {/* Pagination */}
                        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '12px', padding: '16px 0' }}>
                            <button
                                className="btn btn-sm btn-outline"
                                disabled={page <= 1}
                                onClick={() => setPage(p => Math.max(1, p - 1))}
                            >
                                {t('common.previous', 'السابق')}
                            </button>
                            <span style={{ fontSize: '14px', color: '#666' }}>
                                {t('common.page', 'صفحة')} {page}
                            </span>
                            <button
                                className="btn btn-sm btn-outline"
                                disabled={events.length < PAGE_SIZE}
                                onClick={() => setPage(p => p + 1)}
                            >
                                {t('common.next', 'التالي')}
                            </button>
                        </div>
                    </div>
                ) : activeTab === 'attempts' ? (
                    <div className="data-table-container">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>{t('security_events.date')}</th>
                                    <th>{t('security_events.ip_address')}</th>
                                    <th>{t('security_events.username')}</th>
                                    <th>{t('security_events.result')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {loginAttempts.length === 0 ? (
                                    <tr><td colSpan={4} className="text-center p-4">{t('security_events.no_attempts')}</td></tr>
                                ) : loginAttempts.map(la => (
                                    <tr key={la.id}>
                                        <td>{formatDate(la.attempted_at)}</td>
                                        <td><code>{la.ip_address}</code></td>
                                        <td>{la.username || '—'}</td>
                                        <td>
                                            <span className={`badge ${la.success ? 'bg-success' : 'bg-danger'}`}>
                                                {la.success ? t('security_events.success') : t('security_events.failed')}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="data-table-container">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>{t('security_events.ip_address')}</th>
                                    <th>{t('security_events.failed_attempts')}</th>
                                    <th>{t('security_events.last_attempt')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {blockedIPs.length === 0 ? (
                                    <tr><td colSpan={3} className="text-center p-4">{t('security_events.no_blocked_ips')}</td></tr>
                                ) : blockedIPs.map((ip, i) => (
                                    <tr key={i}>
                                        <td><code>{ip.ip_address}</code></td>
                                        <td><span className="badge bg-danger">{ip.failed_attempts}</span></td>
                                        <td>{formatDate(ip.last_attempt)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
};

export default SecurityEvents;
