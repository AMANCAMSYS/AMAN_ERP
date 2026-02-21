import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { hrAdvancedAPI, hrAPI } from '../../utils/api';
import { Plus, Edit2, Star } from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';

import DateInput from '../../components/common/DateInput';
const PerformanceReviews = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const [reviews, setReviews] = useState([]);
    const [employees, setEmployees] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editItem, setEditItem] = useState(null);
    const [form, setForm] = useState({ employee_id: '', review_period: 'annual', review_date: '', performance_score: 3, reviewer_notes: '', goals: '', strengths: '', improvements: '' });

    const periods = [
        { value: 'quarterly', ar: 'ربع سنوي', en: 'Quarterly' },
        { value: 'semi_annual', ar: 'نصف سنوي', en: 'Semi-Annual' },
        { value: 'annual', ar: 'سنوي', en: 'Annual' }
    ];

    const fetchData = async () => {
        setLoading(true);
        try {
            const [rRes, empRes] = await Promise.all([
                hrAdvancedAPI.listPerformanceReviews(),
                hrAPI.listEmployees({ limit: 200 })
            ]);
            setReviews(rRes.data || []);
            setEmployees(empRes.data?.items || empRes.data || []);
        } catch (e) { console.error(e); }
        setLoading(false);
    };

    useEffect(() => { fetchData(); }, []);

    const handleSave = async () => {
        try {
            const payload = { ...form, employee_id: parseInt(form.employee_id), performance_score: parseInt(form.performance_score) };
            if (editItem) {
                await hrAdvancedAPI.updatePerformanceReview(editItem.id, payload);
            } else {
                await hrAdvancedAPI.createPerformanceReview(payload);
            }
            setShowModal(false); setEditItem(null);
            setForm({ employee_id: '', review_period: 'annual', review_date: '', performance_score: 3, reviewer_notes: '', goals: '', strengths: '', improvements: '' });
            fetchData();
        } catch (e) { console.error(e); }
    };

    const renderStars = (score) => {
        return (
            <div style={{ display: 'flex', gap: '2px' }}>
                {[1, 2, 3, 4, 5].map(n => (
                    <Star key={n} size={16} fill={n <= score ? '#f59e0b' : 'none'} color={n <= score ? '#f59e0b' : '#d1d5db'} />
                ))}
            </div>
        );
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div className="header-title">
                    <h1 className="workspace-title">{isRTL ? 'تقييم الأداء' : 'Performance Reviews'}</h1>
                    <p className="workspace-subtitle">{isRTL ? 'تقييم أداء الموظفين' : 'Employee performance evaluations'}</p>
                </div>
                <button className="btn btn-primary" onClick={() => { setEditItem(null); setForm({ employee_id: '', review_period: 'annual', review_date: '', performance_score: 3, reviewer_notes: '', goals: '', strengths: '', improvements: '' }); setShowModal(true); }}>
                    <Plus size={16} /> {isRTL ? 'تقييم جديد' : 'New Review'}
                </button>
            </div>

            <div className="card">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>{isRTL ? 'الموظف' : 'Employee'}</th>
                            <th>{isRTL ? 'الفترة' : 'Period'}</th>
                            <th>{isRTL ? 'التاريخ' : 'Date'}</th>
                            <th>{isRTL ? 'التقييم' : 'Score'}</th>
                            <th>{isRTL ? 'ملاحظات' : 'Notes'}</th>
                            <th>{isRTL ? 'إجراءات' : 'Actions'}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan="7" style={{ textAlign: 'center', padding: '2rem' }}>{isRTL ? 'جاري التحميل...' : 'Loading...'}</td></tr>
                        ) : reviews.length === 0 ? (
                            <tr><td colSpan="7" style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>{isRTL ? 'لا توجد تقييمات' : 'No reviews'}</td></tr>
                        ) : reviews.map((r, i) => (
                            <tr key={r.id}>
                                <td>{i + 1}</td>
                                <td style={{ fontWeight: 600 }}>{r.employee_name || `#${r.employee_id}`}</td>
                                <td>{periods.find(p => p.value === r.review_period)?.[isRTL ? 'ar' : 'en'] || r.review_period}</td>
                                <td>{r.review_date}</td>
                                <td>{renderStars(r.performance_score)}</td>
                                <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.reviewer_notes || '-'}</td>
                                <td>
                                    <button className="btn btn-sm btn-secondary" onClick={() => { setEditItem(r); setForm({ employee_id: r.employee_id, review_period: r.review_period || 'annual', review_date: r.review_date || '', performance_score: r.performance_score || 3, reviewer_notes: r.reviewer_notes || '', goals: r.goals || '', strengths: r.strengths || '', improvements: r.improvements || '' }); setShowModal(true); }}><Edit2 size={14} /></button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 550 }}>
                        <h2 className="modal-title">{editItem ? (isRTL ? 'تعديل تقييم' : 'Edit Review') : (isRTL ? 'تقييم جديد' : 'New Review')}</h2>
                        <div className="form-group">
                            <label>{isRTL ? 'الموظف' : 'Employee'}</label>
                            <select className="form-input" value={form.employee_id} onChange={e => setForm({ ...form, employee_id: e.target.value })}>
                                <option value="">{isRTL ? '-- اختر --' : '-- Select --'}</option>
                                {employees.map(emp => <option key={emp.id} value={emp.id}>{emp.name || emp.full_name}</option>)}
                            </select>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                            <div className="form-group">
                                <label>{isRTL ? 'فترة التقييم' : 'Review Period'}</label>
                                <select className="form-input" value={form.review_period} onChange={e => setForm({ ...form, review_period: e.target.value })}>
                                    {periods.map(p => <option key={p.value} value={p.value}>{isRTL ? p.ar : p.en}</option>)}
                                </select>
                            </div>
                            <div className="form-group">
                                <label>{isRTL ? 'التاريخ' : 'Date'}</label>
                                <DateInput className="form-input" value={form.review_date} onChange={e => setForm({ ...form, review_date: e.target.value })} />
                            </div>
                        </div>
                        <div className="form-group">
                            <label>{isRTL ? 'التقييم (1-5)' : 'Score (1-5)'}</label>
                            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                {[1, 2, 3, 4, 5].map(n => (
                                    <button key={n} type="button" onClick={() => setForm({ ...form, performance_score: n })} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 2 }}>
                                        <Star size={28} fill={n <= form.performance_score ? '#f59e0b' : 'none'} color={n <= form.performance_score ? '#f59e0b' : '#d1d5db'} />
                                    </button>
                                ))}
                                <span style={{ marginInlineStart: '0.5rem', fontWeight: 600, color: '#f59e0b' }}>{form.performance_score}/5</span>
                            </div>
                        </div>
                        <div className="form-group">
                            <label>{isRTL ? 'نقاط القوة' : 'Strengths'}</label>
                            <textarea className="form-input" rows="2" value={form.strengths} onChange={e => setForm({ ...form, strengths: e.target.value })} />
                        </div>
                        <div className="form-group">
                            <label>{isRTL ? 'نقاط التحسين' : 'Improvements'}</label>
                            <textarea className="form-input" rows="2" value={form.improvements} onChange={e => setForm({ ...form, improvements: e.target.value })} />
                        </div>
                        <div className="form-group">
                            <label>{isRTL ? 'ملاحظات المقيّم' : 'Reviewer Notes'}</label>
                            <textarea className="form-input" rows="2" value={form.reviewer_notes} onChange={e => setForm({ ...form, reviewer_notes: e.target.value })} />
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
                            <button className="btn btn-secondary" onClick={() => setShowModal(false)}>{isRTL ? 'إلغاء' : 'Cancel'}</button>
                            <button className="btn btn-primary" onClick={handleSave}>{isRTL ? 'حفظ' : 'Save'}</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PerformanceReviews;
