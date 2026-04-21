import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { hrAdvancedAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import { Eye, CheckSquare } from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';
import { PageLoading } from '../../components/common/LoadingStates'

const TeamReviews = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [reviews, setReviews] = useState([]);
    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState('');

    const cycleId = searchParams.get('cycle_id');

    const fetchReviews = () => {
        setLoading(true);
        const params = {};
        if (cycleId) params.cycle_id = cycleId;
        if (statusFilter) params.status = statusFilter;
        hrAdvancedAPI.listTeamReviews(params)
            .then(res => setReviews(res.data || []))
            .catch(e => toastEmitter.emit(t('common.error'), 'error'))
            .finally(() => setLoading(false));
    };

    useEffect(() => { fetchReviews(); }, [statusFilter, cycleId]);

    const statusBadge = (s) => {
        const colors = {
            pending_self: '#f59e0b',
            pending_manager: '#3b82f6',
            completed: '#16a34a',
        };
        return (
            <span style={{ padding: '2px 10px', borderRadius: 12, fontSize: 12, color: '#fff', background: colors[s] || '#6b7280' }}>
                {t(`performance.status_${s}`, s)}
            </span>
        );
    };

    const getAction = (r) => {
        if (r.status === 'pending_manager') {
            return (
                <button className="btn btn-sm btn-primary" onClick={() => navigate(`/hr/performance/reviews/${r.id}/manager`)}>
                    <CheckSquare size={14} /> {t('performance.manager_review')}
                </button>
            );
        }
        return (
            <button className="btn btn-sm btn-secondary" onClick={() => navigate(`/hr/performance/reviews/${r.id}/result`)}>
                <Eye size={14} /> {t('performance.review_result')}
            </button>
        );
    };

    return (
        <div className="module-container" dir={isRTL ? 'rtl' : 'ltr'}>
            <BackButton />
            <div className="module-header">
                <h1>{t('performance.team_reviews')}</h1>
            </div>

            {/* Status filter */}
            <div style={{ marginBottom: 16 }}>
                <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="form-select" style={{ maxWidth: 220 }}>
                    <option value="">{t('performance.all_statuses')}</option>
                    <option value="pending_self">{t('performance.status_pending_self')}</option>
                    <option value="pending_manager">{t('performance.status_pending_manager')}</option>
                    <option value="completed">{t('performance.status_completed')}</option>
                </select>
            </div>

            {loading ? (
                <PageLoading />
            ) : reviews.length === 0 ? (
                <div className="empty-state">{t('performance.no_reviews')}</div>
            ) : (
                <div className="table-responsive">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>{t('performance.employee')}</th>
                                <th>{t('performance.cycle')}</th>
                                <th>{t('performance.period_label')}</th>
                                <th>{t('performance.composite_score')}</th>
                                <th>{t('performance.status')}</th>
                                <th>{t('common.actions')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {reviews.map(r => (
                                <tr key={r.id}>
                                    <td>{r.employee_name || r.employee_id}</td>
                                    <td>{r.cycle_name || '-'}</td>
                                    <td>{r.review_period || '-'}</td>
                                    <td>{r.composite_score != null ? Number(r.composite_score).toFixed(2) : '-'}</td>
                                    <td>{statusBadge(r.status)}</td>
                                    <td>{getAction(r)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

export default TeamReviews;
