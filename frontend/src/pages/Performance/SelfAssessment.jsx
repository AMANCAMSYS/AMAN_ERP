import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router-dom';
import { hrAdvancedAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import { Star, Send } from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';

const SelfAssessment = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const { id } = useParams();
    const navigate = useNavigate();
    const [review, setReview] = useState(null);
    const [goals, setGoals] = useState([]);
    const [scores, setScores] = useState({});
    const [comments, setComments] = useState({});
    const [overallComments, setOverallComments] = useState('');
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await hrAdvancedAPI.getReviewDetail(id);
                const data = res.data;
                setReview(data);
                setGoals(data.goals || []);
                // Pre-fill if self_assessment exists
                if (data.self_assessment) {
                    const sc = {}; const cm = {};
                    data.self_assessment.forEach(s => {
                        sc[s.goal_id] = s.score;
                        cm[s.goal_id] = s.comments || '';
                    });
                    setScores(sc);
                    setComments(cm);
                    setOverallComments(data.self_comments || '');
                }
            } catch (e) { toastEmitter.emit(t('common.error'), 'error'); }
            setLoading(false);
        };
        fetchData();
    }, [id]);

    const setScore = (goalId, score) => setScores(s => ({ ...s, [goalId]: score }));
    const setComment = (goalId, text) => setComments(c => ({ ...c, [goalId]: text }));

    const handleSubmit = async () => {
        const scoreEntries = goals.map(g => ({
            goal_id: g.id,
            score: scores[g.id] || 0,
            comments: comments[g.id] || '',
        }));

        if (scoreEntries.some(s => s.score === 0)) {
            alert(t('performance.score_all_goals'));
            return;
        }

        setSubmitting(true);
        try {
            await hrAdvancedAPI.submitSelfAssessment(id, {
                scores: scoreEntries,
                overall_comments: overallComments,
            });
            alert(t('performance.self_submitted'));
            navigate('/hr/performance/my-reviews');
        } catch (e) {
            alert(e.response?.data?.detail || 'Error');
        }
        setSubmitting(false);
    };

    const renderStars = (goalId) => {
        const current = scores[goalId] || 0;
        return (
            <div style={{ display: 'flex', gap: 4 }}>
                {[1, 2, 3, 4, 5].map(n => (
                    <Star key={n} size={24} style={{ cursor: 'pointer' }}
                        fill={n <= current ? '#f59e0b' : 'none'}
                        color={n <= current ? '#f59e0b' : '#d1d5db'}
                        onClick={() => setScore(goalId, n)} />
                ))}
            </div>
        );
    };

    if (loading) return <div className="loading-spinner">{t('common.loading')}</div>;
    if (!review) return <div className="empty-state">{t('performance.review_not_found')}</div>;

    const isReadOnly = review.status !== 'pending_self';

    return (
        <div className="module-container" dir={isRTL ? 'rtl' : 'ltr'}>
            <BackButton />
            <h1>{t('performance.self_assessment')}</h1>
            <p style={{ color: '#6b7280', marginBottom: 8 }}>
                {review.cycle_name && <span>{review.cycle_name} — </span>}
                {review.employee_name}
            </p>
            {isReadOnly && (
                <div style={{ padding: '8px 16px', background: '#fef3c7', borderRadius: 8, marginBottom: 16, color: '#92400e' }}>
                    {t('performance.self_already_submitted')}
                </div>
            )}

            {goals.length === 0 ? (
                <div className="empty-state">{t('performance.no_goals')}</div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                    {goals.map((g, idx) => (
                        <div key={g.id} style={{ background: '#f9fafb', padding: 20, borderRadius: 12, border: '1px solid #e5e7eb' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                                <h3 style={{ margin: 0 }}>{idx + 1}. {g.title}</h3>
                                <span style={{ fontSize: 13, color: '#6b7280' }}>
                                    {t('performance.weight')}: {g.weight}%
                                </span>
                            </div>
                            {g.description && <p style={{ color: '#6b7280', fontSize: 14, marginBottom: 8 }}>{g.description}</p>}
                            {g.target && <p style={{ fontSize: 13, color: '#374151' }}><strong>{t('performance.target')}:</strong> {g.target}</p>}

                            <div style={{ marginTop: 12 }}>
                                <label style={{ fontSize: 14, fontWeight: 500 }}>{t('performance.your_score')}</label>
                                {renderStars(g.id)}
                            </div>

                            <div style={{ marginTop: 12 }}>
                                <label style={{ fontSize: 14, fontWeight: 500 }}>{t('performance.your_comments')}</label>
                                <textarea className="form-control" rows={2} disabled={isReadOnly}
                                    value={comments[g.id] || ''}
                                    onChange={e => setComment(g.id, e.target.value)}
                                    placeholder={t('performance.comments_placeholder')} />
                            </div>
                        </div>
                    ))}

                    <div className="form-group">
                        <label style={{ fontWeight: 600 }}>{t('performance.overall_comments')}</label>
                        <textarea className="form-control" rows={3} disabled={isReadOnly}
                            value={overallComments}
                            onChange={e => setOverallComments(e.target.value)}
                            placeholder={t('performance.overall_comments_placeholder')} />
                    </div>

                    {!isReadOnly && (
                        <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting}
                            style={{ alignSelf: 'flex-start' }}>
                            <Send size={16} /> {submitting ? t('common.saving') : t('performance.submit_self')}
                        </button>
                    )}
                </div>
            )}
        </div>
    );
};

export default SelfAssessment;
