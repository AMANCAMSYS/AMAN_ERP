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

    useEffect(() => { fetchData(); }, [activeTab, filter]);

    const fetchData = async () => {
        try {
            setLoading(true);
            if (activeTab === 'events') {
                const [evRes, sumRes] = await Promise.all([
                    securityAPI.listSecurityEvents(filter),
                    securityAPI.getSecurityEventsSummary()
                ]);
                setEvents(evRes.data || []);
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
                            {isRTL ? 'سجل الأحداث الأمنية' : 'Security Events Log'}
                        </h1>
                        <p className="workspace-subtitle">
                            {isRTL ? 'مراقبة الأحداث الأمنية وحماية النظام من الاختراق' : 'Monitor security events and brute force protection'}
                        </p>
                    </div>
                    <button className="btn btn-outline-primary" onClick={fetchData}>
                        <RefreshCw size={16} className="me-1" /> {isRTL ? 'تحديث' : 'Refresh'}
                    </button>
                </div>
            </div>

            {/* Summary Metrics */}
            <div className="metrics-grid mb-4">
                <div className="metric-card">
                    <div className="metric-icon" style={{ background: '#e3f2fd' }}><Activity size={22} color="#1976d2" /></div>
                    <div className="metric-info">
                        <span className="metric-value">{summary.total_events || 0}</span>
                        <span className="metric-label">{isRTL ? 'إجمالي الأحداث' : 'Total Events'}</span>
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-icon" style={{ background: '#fff3e0' }}><AlertTriangle size={22} color="#ef6c00" /></div>
                    <div className="metric-info">
                        <span className="metric-value">{summary.last_24h || 0}</span>
                        <span className="metric-label">{isRTL ? 'آخر 24 ساعة' : 'Last 24 Hours'}</span>
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-icon" style={{ background: '#fce4ec' }}><Lock size={22} color="#c62828" /></div>
                    <div className="metric-info">
                        <span className="metric-value">{blockedIPs.length || 0}</span>
                        <span className="metric-label">{isRTL ? 'عناوين محظورة' : 'Blocked IPs'}</span>
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div className="tabs mb-3">
                {[
                    { key: 'events', label: isRTL ? 'الأحداث الأمنية' : 'Security Events', icon: <Eye size={16} /> },
                    { key: 'attempts', label: isRTL ? 'محاولات الدخول' : 'Login Attempts', icon: <Lock size={16} /> },
                    { key: 'blocked', label: isRTL ? 'عناوين محظورة' : 'Blocked IPs', icon: <AlertTriangle size={16} /> },
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
                        value={filter.severity} onChange={e => setFilter(p => ({ ...p, severity: e.target.value }))}>
                        <option value="">{isRTL ? 'كل مستويات الخطورة' : 'All Severities'}</option>
                        {['critical', 'high', 'medium', 'low', 'info'].map(s => (
                            <option key={s} value={s}>{s}</option>
                        ))}
                    </select>
                    <select className="form-input" style={{ maxWidth: 200 }}
                        value={filter.event_type} onChange={e => setFilter(p => ({ ...p, event_type: e.target.value }))}>
                        <option value="">{isRTL ? 'كل الأنواع' : 'All Types'}</option>
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
                                    <th>{isRTL ? 'التاريخ' : 'Date'}</th>
                                    <th>{isRTL ? 'النوع' : 'Type'}</th>
                                    <th>{isRTL ? 'الخطورة' : 'Severity'}</th>
                                    <th>{isRTL ? 'عنوان IP' : 'IP Address'}</th>
                                    <th>{isRTL ? 'التفاصيل' : 'Details'}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {events.length === 0 ? (
                                    <tr><td colSpan={5} className="text-center p-4">{isRTL ? 'لا توجد أحداث' : 'No events'}</td></tr>
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
                    </div>
                ) : activeTab === 'attempts' ? (
                    <div className="data-table-container">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>{isRTL ? 'التاريخ' : 'Date'}</th>
                                    <th>{isRTL ? 'عنوان IP' : 'IP Address'}</th>
                                    <th>{isRTL ? 'اسم المستخدم' : 'Username'}</th>
                                    <th>{isRTL ? 'النتيجة' : 'Result'}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {loginAttempts.length === 0 ? (
                                    <tr><td colSpan={4} className="text-center p-4">{isRTL ? 'لا توجد محاولات' : 'No attempts'}</td></tr>
                                ) : loginAttempts.map(la => (
                                    <tr key={la.id}>
                                        <td>{formatDate(la.attempted_at)}</td>
                                        <td><code>{la.ip_address}</code></td>
                                        <td>{la.username || '—'}</td>
                                        <td>
                                            <span className={`badge ${la.success ? 'bg-success' : 'bg-danger'}`}>
                                                {la.success ? (isRTL ? 'نجاح' : 'Success') : (isRTL ? 'فشل' : 'Failed')}
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
                                    <th>{isRTL ? 'عنوان IP' : 'IP Address'}</th>
                                    <th>{isRTL ? 'المحاولات الفاشلة' : 'Failed Attempts'}</th>
                                    <th>{isRTL ? 'آخر محاولة' : 'Last Attempt'}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {blockedIPs.length === 0 ? (
                                    <tr><td colSpan={3} className="text-center p-4">{isRTL ? 'لا توجد عناوين محظورة' : 'No blocked IPs'}</td></tr>
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
