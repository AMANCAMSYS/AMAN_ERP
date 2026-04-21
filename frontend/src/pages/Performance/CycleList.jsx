import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { hrAdvancedAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import { Plus, Play, CheckCircle, Clock } from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';
import { PageLoading } from '../../components/common/LoadingStates'

const CycleList = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const navigate = useNavigate();
    const [cycles, setCycles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState('');

    const fetchCycles = async () => {
        setLoading(true);
        try {
            const params = {};
            if (statusFilter) params.status = statusFilter;
            const res = await hrAdvancedAPI.listCycles(params);
            setCycles(res.data || []);
        } catch (e) { toastEmitter.emit(t('common.error'), 'error'); }
        setLoading(false);
    };

    useEffect(() => { fetchCycles(); }, [statusFilter]);

    const handleLaunch = async (id) => {
        if (!window.confirm(t('performance.confirm_launch'))) return;
        try {
            await hrAdvancedAPI.launchCycle(id);
            fetchCycles();
        } catch (e) {
            alert(e.response?.data?.detail || 'Error');
        }
    };

    const statusBadge = (s) => {
        const colors = { draft: '#6b7280', active: '#2563eb', completed: '#16a34a' };
        return (
            <span style={{ padding: '2px 10px', borderRadius: 12, fontSize: 12, color: '#fff', background: colors[s] || '#6b7280' }}>
                {t(`performance.status_${s}`)}
            </span>
        );
    };

    // KPI cards
    const total = cycles.length;
    const active = cycles.filter(c => c.status === 'active').length;
    const totalReviews = cycles.reduce((s, c) => s + (c.total_reviews || 0), 0);
    const completedReviews = cycles.reduce((s, c) => s + (c.completed_reviews || 0), 0);

    return (
        <div className="module-container" dir={isRTL ? 'rtl' : 'ltr'}>
            <BackButton />
            <div className="module-header">
                <h1>{t('performance.cycles_title')}</h1>
                <button className="btn btn-primary" onClick={() => navigate('/hr/performance/cycle-new')}>
                    <Plus size={16} /> {t('performance.new_cycle')}
                </button>
            </div>

            {/* KPI Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 24 }}>
                <div className="stat-card"><div className="stat-value">{total}</div><div className="stat-label">{t('performance.total_cycles')}</div></div>
                <div className="stat-card"><div className="stat-value">{active}</div><div className="stat-label">{t('performance.active_cycles')}</div></div>
                <div className="stat-card"><div className="stat-value">{totalReviews}</div><div className="stat-label">{t('performance.total_reviews')}</div></div>
                <div className="stat-card"><div className="stat-value">{completedReviews}</div><div className="stat-label">{t('performance.completed_reviews')}</div></div>
            </div>

            {/* Filter */}
            <div style={{ marginBottom: 16 }}>
                <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="form-select" style={{ maxWidth: 200 }}>
                    <option value="">{t('performance.all_statuses')}</option>
                    <option value="draft">{t('performance.status_draft')}</option>
                    <option value="active">{t('performance.status_active')}</option>
                    <option value="completed">{t('performance.status_completed')}</option>
                </select>
            </div>

            {loading ? (
                <PageLoading />
            ) : cycles.length === 0 ? (
                <div className="empty-state">{t('performance.no_cycles')}</div>
            ) : (
                <div className="table-responsive">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>{t('performance.cycle_name')}</th>
                                <th>{t('performance.period')}</th>
                                <th>{t('performance.self_deadline')}</th>
                                <th>{t('performance.manager_deadline')}</th>
                                <th>{t('performance.status')}</th>
                                <th>{t('performance.progress')}</th>
                                <th>{t('common.actions')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {cycles.map(c => (
                                <tr key={c.id} style={{ cursor: 'pointer' }}>
                                    <td>{c.name}</td>
                                    <td>{c.period_start} — {c.period_end}</td>
                                    <td>{c.self_assessment_deadline || '-'}</td>
                                    <td>{c.manager_review_deadline || '-'}</td>
                                    <td>{statusBadge(c.status)}</td>
                                    <td>{c.completed_reviews || 0} / {c.total_reviews || 0}</td>
                                    <td>
                                        {c.status === 'draft' && (
                                            <button className="btn btn-sm btn-success" onClick={() => handleLaunch(c.id)} title={t('performance.launch')}>
                                                <Play size={14} />
                                            </button>
                                        )}
                                        {c.status === 'active' && (
                                            <button className="btn btn-sm btn-info" onClick={() => navigate(`/hr/performance/team-reviews?cycle_id=${c.id}`)} title={t('performance.view_reviews')}>
                                                <CheckCircle size={14} />
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
    );
};

export default CycleList;
