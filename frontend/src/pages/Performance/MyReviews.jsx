import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { hrAdvancedAPI } from '../../utils/api';
import { Eye, ClipboardList } from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';

const MyReviews = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const navigate = useNavigate();
    const [reviews, setReviews] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        hrAdvancedAPI.listMyReviews()
            .then(res => setReviews(res.data || []))
            .catch(e => console.error(e))
            .finally(() => setLoading(false));
    }, []);

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
        if (r.status === 'pending_self') {
            return (
                <button className="btn btn-sm btn-primary" onClick={() => navigate(`/hr/performance/reviews/${r.id}/self`)}>
                    <ClipboardList size={14} /> {t('performance.self_assessment')}
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
                <h1>{t('performance.my_reviews')}</h1>
            </div>

            {loading ? (
                <div className="loading-spinner">{t('common.loading')}</div>
            ) : reviews.length === 0 ? (
                <div className="empty-state">{t('performance.no_reviews')}</div>
            ) : (
                <div className="table-responsive">
                    <table className="data-table">
                        <thead>
                            <tr>
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

export default MyReviews;
