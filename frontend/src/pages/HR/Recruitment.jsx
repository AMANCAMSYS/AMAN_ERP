import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { hrImprovementsAPI } from '../../utils/api';
import { useToast } from '../../context/ToastContext';
import { Briefcase, Users, Plus, ArrowRight, UserCheck, Clock, X, CheckCircle } from 'lucide-react';
import '../../components/ModuleStyles.css';

import DateInput from '../../components/common/DateInput';
const Recruitment = () => {
    const { t, i18n } = useTranslation();
    const { showToast } = useToast();
    const isRTL = i18n.language === 'ar';
    const [activeTab, setActiveTab] = useState('openings');
    const [openings, setOpenings] = useState([]);
    const [applications, setApplications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [modalType, setModalType] = useState('opening');

    const [openingForm, setOpeningForm] = useState({ title: '', department: '', positions: 1, requirements: '', deadline: '' });
    const [appForm, setAppForm] = useState({ job_opening_id: '', applicant_name: '', email: '', phone: '', resume_url: '' });

    useEffect(() => { fetchData(); }, [activeTab]);

    const fetchData = async () => {
        try {
            setLoading(true);
            if (activeTab === 'openings') { const res = await hrImprovementsAPI.listJobOpenings(); setOpenings(res.data || []); }
            else { const res = await hrImprovementsAPI.listAllApplications(); setApplications(res.data || []); }
        } catch (err) { console.error(err); } finally { setLoading(false); }
    };

    const handleCreateOpening = async (e) => {
        e.preventDefault();
        try {
            await hrImprovementsAPI.createJobOpening({ ...openingForm, positions: parseInt(openingForm.positions) });
            showToast(t('hr.job_opening_created'), 'success');
            setShowModal(false); fetchData();
        } catch (err) { showToast(err.response?.data?.detail || t('common.error'), 'error'); }
    };

    const handleCreateApplication = async (e) => {
        e.preventDefault();
        try {
            await hrImprovementsAPI.createApplication({ ...appForm, job_opening_id: parseInt(appForm.job_opening_id) });
            showToast(t('hr.application_submitted'), 'success');
            setShowModal(false); fetchData();
        } catch (err) { showToast(err.response?.data?.detail || t('common.error'), 'error'); }
    };

    const handleUpdateStage = async (appId, stage) => {
        try {
            await hrImprovementsAPI.updateApplicationStage(appId, stage);
            showToast(t('hr.stage_updated'), 'success');
            fetchData();
        } catch (err) { showToast(t('common.error'), 'error'); }
    };

    const statusBadge = (status) => {
        const map = {
            open: { cls: 'bg-green-100 text-green-700', label: t('hr.status_open') },
            closed: { cls: 'bg-gray-100 text-gray-700', label: t('hr.status_closed') },
            new: { cls: 'bg-blue-100 text-blue-700', label: t('hr.stage_new') },
            screening: { cls: 'bg-yellow-100 text-yellow-700', label: t('hr.stage_screening') },
            interview: { cls: 'bg-purple-100 text-purple-700', label: t('hr.stage_interview') },
            offer: { cls: 'bg-orange-100 text-orange-700', label: t('hr.stage_offer') },
            hired: { cls: 'bg-green-100 text-green-700', label: t('hr.stage_hired') },
            rejected: { cls: 'bg-red-100 text-red-700', label: t('hr.stage_rejected') },
        };
        const conf = map[status] || { cls: 'bg-gray-100 text-gray-700', label: status };
        return <span className={`badge ${conf.cls}`}>{conf.label}</span>;
    };

    const stages = ['new', 'screening', 'interview', 'offer', 'hired', 'rejected'];

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className="workspace-title"><span className="p-2 rounded-lg bg-indigo-50 text-indigo-600"><Briefcase size={24} /></span> {t('hr.recruitment_title')}</h1>
                        <p className="workspace-subtitle">{t('hr.recruitment_subtitle')}</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => { setModalType(activeTab === 'openings' ? 'opening' : 'application'); setShowModal(true); }}>
                        <Plus size={18} /> {activeTab === 'openings' ? (t('hr.new_opening')) : (t('hr.new_application'))}
                    </button>
                </div>
            </div>

            <div className="d-flex gap-2 mb-4">
                <button onClick={() => setActiveTab('openings')} className={`btn ${activeTab === 'openings' ? 'btn-primary' : 'btn-secondary'}`}><Briefcase size={16} /> {t('hr.tab_openings')}</button>
                <button onClick={() => setActiveTab('applications')} className={`btn ${activeTab === 'applications' ? 'btn-primary' : 'btn-secondary'}`}><Users size={16} /> {t('hr.tab_applications')}</button>
            </div>

            <div className="card section-card">
                {loading ? <div className="text-center p-4">...</div> : activeTab === 'openings' ? (
                    <div className="data-table-container">
                        <table className="data-table">
                            <thead><tr>
                                <th>{t('hr.col_title')}</th>
                                <th>{t('hr.col_department')}</th>
                                <th>{t('hr.col_positions')}</th>
                                <th>{t('hr.col_deadline')}</th>
                                <th>{t('hr.col_status')}</th>
                            </tr></thead>
                            <tbody>
                                {openings.map(o => (
                                    <tr key={o.id}>
                                        <td className="font-medium">{o.title}</td>
                                        <td>{o.department || '—'}</td>
                                        <td className="text-center">{o.positions}</td>
                                        <td>{o.deadline || '—'}</td>
                                        <td>{statusBadge(o.status || 'open')}</td>
                                    </tr>
                                ))}
                                {openings.length === 0 && <tr><td colSpan="5" className="text-center text-muted p-4">{t('hr.no_openings')}</td></tr>}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="data-table-container">
                        <table className="data-table">
                            <thead><tr>
                                <th>{t('hr.col_applicant')}</th>
                                <th>{t('hr.col_email')}</th>
                                <th>{t('hr.col_job')}</th>
                                <th>{t('hr.col_stage')}</th>
                                <th>{t('hr.col_actions')}</th>
                            </tr></thead>
                            <tbody>
                                {applications.map(a => (
                                    <tr key={a.id}>
                                        <td className="font-medium">{a.applicant_name}</td>
                                        <td>{a.email || '—'}</td>
                                        <td>{a.opening_title || `#${a.opening_id}`}</td>
                                        <td>{statusBadge(a.stage || 'new')}</td>
                                        <td>
                                            <div className="d-flex gap-1">
                                                {stages.filter(s => s !== a.stage).slice(0, 3).map(s => (
                                                    <button key={s} className="btn btn-sm btn-secondary" title={s} onClick={() => handleUpdateStage(a.id, s)}>{s === 'hired' ? <CheckCircle size={12} /> : s === 'rejected' ? <X size={12} /> : <ArrowRight size={12} />} <span className="text-xs">{s}</span></button>
                                                ))}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                                {applications.length === 0 && <tr><td colSpan="5" className="text-center text-muted p-4">{t('hr.no_applications')}</td></tr>}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Job Opening Modal */}
            {showModal && modalType === 'opening' && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                            <h3 className="modal-title" style={{ margin: 0 }}>{t('hr.new_job_opening_modal')}</h3>
                            <button type="button" onClick={() => setShowModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 20, color: 'var(--text-muted)' }}>✕</button>
                        </div>
                        <form onSubmit={handleCreateOpening} className="space-y-4">
                            <div className="form-group">
                                <label className="form-label">{t('hr.job_title')}</label>
                                <input className="form-input" required value={openingForm.title} onChange={e => setOpeningForm({ ...openingForm, title: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('hr.col_department')}</label>
                                <input className="form-input" value={openingForm.department} onChange={e => setOpeningForm({ ...openingForm, department: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('hr.positions_count')}</label>
                                <input type="number" className="form-input" min="1" required value={openingForm.positions} onChange={e => setOpeningForm({ ...openingForm, positions: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('hr.requirements')}</label>
                                <textarea className="form-input" rows="3" value={openingForm.requirements} onChange={e => setOpeningForm({ ...openingForm, requirements: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('hr.deadline')}</label>
                                <DateInput value={openingForm.deadline} onChange={e => setOpeningForm({ ...openingForm, deadline: e.target.value })} />
                            </div>
                            <div className="d-flex gap-3 pt-3">
                                <button type="submit" className="btn btn-primary flex-1">{t('hr.create')}</button>
                                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>{t('hr.cancel')}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Application Modal */}
            {showModal && modalType === 'application' && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                            <h3 className="modal-title" style={{ margin: 0 }}>{t('hr.new_application_modal')}</h3>
                            <button type="button" onClick={() => setShowModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 20, color: 'var(--text-muted)' }}>✕</button>
                        </div>
                        <form onSubmit={handleCreateApplication} className="space-y-4">
                            <div className="form-group">
                                <label className="form-label">{t('hr.job_opening_id')}</label>
                                <input type="number" className="form-input" required value={appForm.job_opening_id} onChange={e => setAppForm({ ...appForm, job_opening_id: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('hr.applicant_name')}</label>
                                <input className="form-input" required value={appForm.applicant_name} onChange={e => setAppForm({ ...appForm, applicant_name: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('hr.col_email')}</label>
                                <input type="email" className="form-input" value={appForm.email} onChange={e => setAppForm({ ...appForm, email: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('hr.phone')}</label>
                                <input className="form-input" value={appForm.phone} onChange={e => setAppForm({ ...appForm, phone: e.target.value })} />
                            </div>
                            <div className="d-flex gap-3 pt-3">
                                <button type="submit" className="btn btn-primary flex-1">{t('hr.submit')}</button>
                                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>{t('hr.cancel')}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Recruitment;
