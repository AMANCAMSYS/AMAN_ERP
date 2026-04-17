import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { hrAdvancedAPI, hrAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import { Plus, Edit2, Users, BookOpen } from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';

import DateInput from '../../components/common/DateInput';
import { formatDate, formatDateTime } from '../../utils/dateUtils';
import BackButton from '../../components/common/BackButton';
const TrainingPrograms = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const [programs, setPrograms] = useState([]);
    const [employees, setEmployees] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [showParticipantsModal, setShowParticipantsModal] = useState(false);
    const [selectedProgram, setSelectedProgram] = useState(null);
    const [participants, setParticipants] = useState([]);
    const [editItem, setEditItem] = useState(null);
    const [form, setForm] = useState({ name: '', name_en: '', description: '', trainer: '', start_date: '', end_date: '', location: '', max_participants: 20 });
    const [partForm, setPartForm] = useState({ employee_id: '' });

    const fetchData = async () => {
        setLoading(true);
        try {
            const [pRes, empRes] = await Promise.all([
                hrAdvancedAPI.listTraining(),
                hrAPI.listEmployees({ limit: 200 })
            ]);
            setPrograms(pRes.data || []);
            setEmployees(empRes.data?.items || empRes.data || []);
        } catch (e) { toastEmitter.emit(t('common.error'), 'error'); }
        setLoading(false);
    };

    useEffect(() => { fetchData(); }, []);

    const handleSave = async () => {
        try {
            const payload = { ...form, max_participants: parseInt(form.max_participants) || 20 };
            if (editItem) {
                await hrAdvancedAPI.updateTraining(editItem.id, payload);
            } else {
                await hrAdvancedAPI.createTraining(payload);
            }
            setShowModal(false); setEditItem(null);
            setForm({ name: '', name_en: '', description: '', trainer: '', start_date: '', end_date: '', location: '', max_participants: 20 });
            fetchData();
        } catch (e) { toastEmitter.emit(t('common.error'), 'error'); }
    };

    const openParticipants = async (program) => {
        setSelectedProgram(program);
        try {
            const res = await hrAdvancedAPI.listParticipants(program.id);
            setParticipants(res.data || []);
        } catch (e) { setParticipants([]); }
        setShowParticipantsModal(true);
    };

    const addParticipant = async () => {
        if (!partForm.employee_id) return;
        try {
            await hrAdvancedAPI.addParticipant(selectedProgram.id, { employee_id: parseInt(partForm.employee_id) });
            const res = await hrAdvancedAPI.listParticipants(selectedProgram.id);
            setParticipants(res.data || []);
            setPartForm({ employee_id: '' });
        } catch (e) { toastEmitter.emit(t('common.error'), 'error'); }
    };

    const getStatusBadge = (status) => {
        const map = {
            planned: { cls: 'badge-info', ar: 'مخطط', en: 'Planned' },
            in_progress: { cls: 'badge-warning', ar: 'جاري', en: 'In Progress' },
            completed: { cls: 'badge-success', ar: 'مكتمل', en: 'Completed' },
            cancelled: { cls: 'badge-danger', ar: 'ملغي', en: 'Cancelled' }
        };
        const s = map[status] || map.planned;
        return <span className={`badge ${s.cls}`}>{isRTL ? s.ar : s.en}</span>;
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">{t('hr.training.training_programs')}</h1>
                    <p className="workspace-subtitle">{t('hr.training.manage_employee_training_programs')}</p>
                </div>
                <button className="btn btn-primary" onClick={() => { setEditItem(null); setForm({ name: '', name_en: '', description: '', trainer: '', start_date: '', end_date: '', location: '', max_participants: 20 }); setShowModal(true); }}>
                    <Plus size={16} /> {t('hr.training.new_program')}
                </button>
            </div>

            <div className="card">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>{t('hr.training.program')}</th>
                            <th>{t('hr.training.trainer')}</th>
                            <th>{t('hr.training.from')}</th>
                            <th>{t('hr.training.to')}</th>
                            <th>{t('hr.training.location')}</th>
                            <th>{t('hr.training.status')}</th>
                            <th>{t('hr.training.actions')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan="8" style={{ textAlign: 'center', padding: '2rem' }}>{t('hr.training.loading')}</td></tr>
                        ) : programs.length === 0 ? (
                            <tr><td colSpan="8" style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>{t('hr.training.no_training_programs')}</td></tr>
                        ) : programs.map((p, i) => (
                            <tr key={p.id}>
                                <td>{i + 1}</td>
                                <td style={{ fontWeight: 600 }}>{p.name}</td>
                                <td>{p.trainer || '-'}</td>
                                <td>{formatDate(p.start_date)}</td>
                                <td>{formatDate(p.end_date)}</td>
                                <td>{p.location || '-'}</td>
                                <td>{getStatusBadge(p.status)}</td>
                                <td>
                                    <div style={{ display: 'flex', gap: '0.25rem' }}>
                                        <button className="btn btn-sm btn-secondary" onClick={() => openParticipants(p)} title={t('hr.training.participants')}><Users size={14} /></button>
                                        <button className="btn btn-sm btn-secondary" onClick={() => { setEditItem(p); setForm({ name: p.name, name_en: p.name_en || '', description: p.description || '', trainer: p.trainer || '', start_date: p.start_date || '', end_date: p.end_date || '', location: p.location || '', max_participants: p.max_participants || 20 }); setShowModal(true); }}><Edit2 size={14} /></button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Program modal */}
            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 550 }}>
                        <h2 className="modal-title">{editItem ? (t('hr.training.edit_program')) : (t('hr.training.new_program'))}</h2>
                        <div className="form-group">
                            <label>{t('hr.training.program_name')}</label>
                            <input className="form-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
                        </div>
                        <div className="form-group">
                            <label>{t('hr.training.name_en')}</label>
                            <input className="form-input" value={form.name_en} onChange={e => setForm({ ...form, name_en: e.target.value })} />
                        </div>
                        <div className="form-group">
                            <label>{t('hr.training.trainer')}</label>
                            <input className="form-input" value={form.trainer} onChange={e => setForm({ ...form, trainer: e.target.value })} />
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                            <div className="form-group">
                                <label>{t('hr.training.start_date')}</label>
                                <DateInput className="form-input" value={form.start_date} onChange={e => setForm({ ...form, start_date: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>{t('hr.training.end_date')}</label>
                                <DateInput className="form-input" value={form.end_date} onChange={e => setForm({ ...form, end_date: e.target.value })} />
                            </div>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '0.75rem' }}>
                            <div className="form-group">
                                <label>{t('hr.training.location')}</label>
                                <input className="form-input" value={form.location} onChange={e => setForm({ ...form, location: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>{t('hr.training.max')}</label>
                                <input type="number" className="form-input" value={form.max_participants} onChange={e => setForm({ ...form, max_participants: e.target.value })} />
                            </div>
                        </div>
                        <div className="form-group">
                            <label>{t('hr.training.description')}</label>
                            <textarea className="form-input" rows="2" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
                            <button className="btn btn-secondary" onClick={() => setShowModal(false)}>{t('hr.training.cancel')}</button>
                            <button className="btn btn-primary" onClick={handleSave}>{t('hr.training.save')}</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Participants modal */}
            {showParticipantsModal && (
                <div className="modal-overlay" onClick={() => setShowParticipantsModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
                        <h2 className="modal-title">{isRTL ? `المشاركون - ${selectedProgram?.name}` : `Participants - ${selectedProgram?.name}`}</h2>
                        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                            <select className="form-input" value={partForm.employee_id} onChange={e => setPartForm({ employee_id: e.target.value })} style={{ flex: 1 }}>
                                <option value="">{t('hr.training.select_employee')}</option>
                                {employees.map(emp => <option key={emp.id} value={emp.id}>{emp.name || emp.full_name}</option>)}
                            </select>
                            <button className="btn btn-primary" onClick={addParticipant}><Plus size={16} /></button>
                        </div>
                        {participants.length === 0 ? (
                            <p style={{ textAlign: 'center', color: '#666', padding: '1rem' }}>{t('hr.training.no_participants')}</p>
                        ) : (
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>{t('hr.training.employee')}</th>
                                        <th>{t('hr.training.status')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {participants.map((p, i) => (
                                        <tr key={p.id || i}>
                                            <td>{i + 1}</td>
                                            <td>{p.employee_name || `#${p.employee_id}`}</td>
                                            <td><span className={`badge ${p.status === 'completed' ? 'badge-success' : 'badge-info'}`}>{p.status === 'completed' ? (t('hr.training.completed')) : (t('hr.training.enrolled'))}</span></td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
                            <button className="btn btn-secondary" onClick={() => setShowParticipantsModal(false)}>{t('hr.training.close')}</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TrainingPrograms;
