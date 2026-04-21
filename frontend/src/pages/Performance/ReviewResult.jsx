import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import { hrAdvancedAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import { Star, Award, Target, BarChart3 } from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';
import { PageLoading } from '../../components/common/LoadingStates'

const ReviewResult = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const { id } = useParams();
    const [review, setReview] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchReview = async () => {
            try {
                const res = await hrAdvancedAPI.getReviewDetail(id);
                setReview(res.data);
            } catch (e) { toastEmitter.emit(t('common.error'), 'error'); }
            setLoading(false);
        };
        fetchReview();
    }, [id]);

    if (loading) return <PageLoading />;
    if (!review) return <div className="empty-state">{t('performance.review_not_found')}</div>;

    const goals = review.goals || [];
    const selfScores = {};
    const mgrScores = {};
    if (review.self_assessment) review.self_assessment.forEach(s => { selfScores[s.goal_id] = s; });
    if (review.manager_assessment) review.manager_assessment.forEach(s => { mgrScores[s.goal_id] = s; });

    const renderStarRow = (score, color = '#f59e0b') => (
        <div style={{ display: 'flex', gap: 2 }}>
            {[1, 2, 3, 4, 5].map(n => (
                <Star key={n} size={16} fill={n <= (score || 0) ? color : 'none'} color={n <= (score || 0) ? color : '#d1d5db'} />
            ))}
            <span style={{ marginLeft: 8, fontWeight: 600, fontSize: 14 }}>{score || '-'}</span>
        </div>
    );

    const scoreColor = (score) => {
        if (!score) return '#6b7280';
        if (score >= 4) return '#16a34a';
        if (score >= 3) return '#2563eb';
        if (score >= 2) return '#f59e0b';
        return '#dc2626';
    };

    return (
        <div className="module-container" dir={isRTL ? 'rtl' : 'ltr'}>
            <BackButton />

            {/* Header */}
            <div style={{ marginBottom: 24 }}>
                <h1>{t('performance.review_result')}</h1>
                <p style={{ color: '#6b7280' }}>
                    {review.employee_name}
                    {review.cycle_name && ` — ${review.cycle_name}`}
                    {review.review_period && ` (${review.review_period})`}
                </p>
            </div>

            {/* Score Summary Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 32 }}>
                <div className="stat-card">
                    <Award size={28} color={scoreColor(review.composite_score)} />
                    <div className="stat-value" style={{ color: scoreColor(review.composite_score), fontSize: 36 }}>
                        {review.composite_score != null ? Number(review.composite_score).toFixed(2) : '-'}
                    </div>
                    <div className="stat-label">{t('performance.composite_score')}</div>
                </div>
                <div className="stat-card">
                    <Target size={28} color="#2563eb" />
                    <div className="stat-value">{goals.length}</div>
                    <div className="stat-label">{t('performance.total_goals')}</div>
                </div>
                <div className="stat-card">
                    <BarChart3 size={28} color="#8b5cf6" />
                    <div className="stat-value">
                        {review.status === 'completed'
                            ? t('performance.status_completed')
                            : t(`performance.status_${review.status}`)}
                    </div>
                    <div className="stat-label">{t('performance.status')}</div>
                </div>
            </div>

            {/* Goals Breakdown */}
            {goals.length > 0 && (
                <>
                    <h2 style={{ marginBottom: 16 }}>{t('performance.goals_breakdown')}</h2>
                    <div className="table-responsive">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>{t('performance.goal_title')}</th>
                                    <th>{t('performance.weight')}</th>
                                    <th>{t('performance.target')}</th>
                                    <th>{t('performance.self_score')}</th>
                                    <th>{t('performance.manager_score')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {goals.map((g, idx) => (
                                    <tr key={g.id}>
                                        <td>{idx + 1}</td>
                                        <td>
                                            <strong>{g.title}</strong>
                                            {g.description && <div style={{ fontSize: 12, color: '#6b7280' }}>{g.description}</div>}
                                        </td>
                                        <td>{g.weight}%</td>
                                        <td>{g.target || '-'}</td>
                                        <td>
                                            {selfScores[g.id]
                                                ? renderStarRow(selfScores[g.id].score, '#3b82f6')
                                                : <span style={{ color: '#9ca3af' }}>-</span>}
                                            {selfScores[g.id]?.comments && (
                                                <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>{selfScores[g.id].comments}</div>
                                            )}
                                        </td>
                                        <td>
                                            {mgrScores[g.id]
                                                ? renderStarRow(mgrScores[g.id].score, '#f59e0b')
                                                : <span style={{ color: '#9ca3af' }}>-</span>}
                                            {mgrScores[g.id]?.comments && (
                                                <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>{mgrScores[g.id].comments}</div>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </>
            )}

            {/* Comments Section */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginTop: 32 }}>
                <div style={{ background: '#eff6ff', padding: 20, borderRadius: 12 }}>
                    <h3>{t('performance.employee_comments')}</h3>
                    <p style={{ color: '#374151' }}>{review.self_comments || t('performance.no_comments')}</p>
                </div>
                <div style={{ background: '#fef3c7', padding: 20, borderRadius: 12 }}>
                    <h3>{t('performance.manager_comments')}</h3>
                    <p style={{ color: '#374151' }}>{review.manager_comments || t('performance.no_comments')}</p>
                </div>
            </div>
            {review.final_comments && (
                <div style={{ background: '#dcfce7', padding: 20, borderRadius: 12, marginTop: 16 }}>
                    <h3>{t('performance.final_comments')}</h3>
                    <p style={{ color: '#374151' }}>{review.final_comments}</p>
                </div>
            )}
        </div>
    );
};

export default ReviewResult;
