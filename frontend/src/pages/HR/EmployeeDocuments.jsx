import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { hrAdvancedAPI, hrAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import { Plus, Edit2, Trash2, AlertTriangle, FileText } from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';

import DateInput from '../../components/common/DateInput';
import BackButton from '../../components/common/BackButton';
const EmployeeDocuments = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const [docs, setDocs] = useState([]);
    const [employees, setEmployees] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editItem, setEditItem] = useState(null);
    const [form, setForm] = useState({ employee_id: '', document_type: 'passport', document_number: '', issue_date: '', expiry_date: '', notes: '' });

    const docTypes = [
        { value: 'passport', ar: 'جواز سفر', en: 'Passport' },
        { value: 'iqama', ar: 'إقامة', en: 'Iqama' },
        { value: 'driving_license', ar: 'رخصة قيادة', en: 'Driving License' },
        { value: 'national_id', ar: 'هوية وطنية', en: 'National ID' },
        { value: 'certificate', ar: 'شهادة', en: 'Certificate' },
        { value: 'contract', ar: 'عقد', en: 'Contract' },
        { value: 'other', ar: 'أخرى', en: 'Other' }
    ];

    const fetchData = async () => {
        setLoading(true);
        try {
            const [dRes, empRes] = await Promise.all([
                hrAdvancedAPI.listDocuments(),
                hrAPI.listEmployees({ limit: 200 })
            ]);
            setDocs(dRes.data || []);
            setEmployees(empRes.data?.items || empRes.data || []);
        } catch (e) { toastEmitter.emit(t('common.error'), 'error'); }
        setLoading(false);
    };

    useEffect(() => { fetchData(); }, []);

    const handleSave = async () => {
        try {
            const payload = { ...form, employee_id: parseInt(form.employee_id) };
            if (editItem) {
                await hrAdvancedAPI.updateDocument(editItem.id, payload);
            } else {
                await hrAdvancedAPI.createDocument(payload);
            }
            setShowModal(false);
            setEditItem(null);
            setForm({ employee_id: '', document_type: 'passport', document_number: '', issue_date: '', expiry_date: '', notes: '' });
            fetchData();
        } catch (e) { toastEmitter.emit(t('common.error'), 'error'); }
    };

    const handleDelete = async (id) => {
        if (!window.confirm(t('hr.documents.are_you_sure'))) return;
        try { await hrAdvancedAPI.deleteDocument(id); fetchData(); } catch (e) { toastEmitter.emit(t('common.error'), 'error'); }
    };

    const getDaysUntilExpiry = (expiryDate) => {
        if (!expiryDate) return null;
        const diff = Math.ceil((new Date(expiryDate) - new Date()) / (1000 * 60 * 60 * 24));
        return diff;
    };

    const getExpiryBadge = (expiryDate) => {
        const days = getDaysUntilExpiry(expiryDate);
        if (days === null) return null;
        if (days < 0) return <span className="badge badge-danger">{t('hr.documents.expired')}</span>;
        if (days <= 30) return <span className="badge badge-danger">{isRTL ? `${days} يوم` : `${days} days`}</span>;
        if (days <= 60) return <span className="badge badge-warning">{isRTL ? `${days} يوم` : `${days} days`}</span>;
        if (days <= 90) return <span className="badge badge-info">{isRTL ? `${days} يوم` : `${days} days`}</span>;
        return <span className="badge badge-success">{t('hr.documents.valid')}</span>;
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">{t('hr.documents.employee_documents')}</h1>
                    <p className="workspace-subtitle">{t('hr.documents.track_passports_iqamas_and_documents')}</p>
                </div>
                <button className="btn btn-primary" onClick={() => { setEditItem(null); setForm({ employee_id: '', document_type: 'passport', document_number: '', issue_date: '', expiry_date: '', notes: '' }); setShowModal(true); }}>
                    <Plus size={16} /> {t('hr.documents.new_document')}
                </button>
            </div>

            {/* Expiry alerts */}
            {docs.filter(d => { const days = getDaysUntilExpiry(d.expiry_date); return days !== null && days <= 90; }).length > 0 && (
                <div className="card" style={{ background: '#fff3cd', borderColor: '#ffc107', marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#856404' }}>
                        <AlertTriangle size={20} />
                        <strong>{t('hr.documents.warning_documents_expiring_soon')}</strong>
                    </div>
                </div>
            )}

            <div className="card">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>{t('hr.documents.employee')}</th>
                            <th>{t('hr.documents.type')}</th>
                            <th>{t('hr.documents.doc_number')}</th>
                            <th>{t('hr.documents.issue_date')}</th>
                            <th>{t('hr.documents.expiry_date')}</th>
                            <th>{t('hr.documents.status')}</th>
                            <th>{t('hr.documents.actions')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan="8" style={{ textAlign: 'center', padding: '2rem' }}>{t('hr.documents.loading')}</td></tr>
                        ) : docs.length === 0 ? (
                            <tr><td colSpan="8" style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>{t('hr.documents.no_documents')}</td></tr>
                        ) : docs.map((d, i) => (
                            <tr key={d.id} style={getDaysUntilExpiry(d.expiry_date) !== null && getDaysUntilExpiry(d.expiry_date) <= 30 ? { background: '#fff5f5' } : {}}>
                                <td>{i + 1}</td>
                                <td style={{ fontWeight: 600 }}>{d.employee_name || `#${d.employee_id}`}</td>
                                <td>{docTypes.find(dt => dt.value === d.document_type)?.[t('hr.documents.en')] || d.document_type}</td>
                                <td>{d.document_number}</td>
                                <td>{d.issue_date || '-'}</td>
                                <td>{d.expiry_date || '-'}</td>
                                <td>{getExpiryBadge(d.expiry_date)}</td>
                                <td>
                                    <div style={{ display: 'flex', gap: '0.25rem' }}>
                                        <button className="btn btn-sm btn-secondary" onClick={() => { setEditItem(d); setForm({ employee_id: d.employee_id, document_type: d.document_type, document_number: d.document_number || '', issue_date: d.issue_date || '', expiry_date: d.expiry_date || '', notes: d.notes || '' }); setShowModal(true); }}><Edit2 size={14} /></button>
                                        <button className="btn btn-sm btn-danger" onClick={() => handleDelete(d.id)}><Trash2 size={14} /></button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
                        <h2 className="modal-title">{editItem ? (t('hr.documents.edit_document')) : (t('hr.documents.new_document'))}</h2>
                        <div className="form-group">
                            <label>{t('hr.documents.employee')}</label>
                            <select className="form-input" value={form.employee_id} onChange={e => setForm({ ...form, employee_id: e.target.value })}>
                                <option value="">{t('hr.documents.select')}</option>
                                {employees.map(emp => <option key={emp.id} value={emp.id}>{emp.name || emp.full_name}</option>)}
                            </select>
                        </div>
                        <div className="form-group">
                            <label>{t('hr.documents.document_type')}</label>
                            <select className="form-input" value={form.document_type} onChange={e => setForm({ ...form, document_type: e.target.value })}>
                                {docTypes.map(dt => <option key={dt.value} value={dt.value}>{isRTL ? dt.ar : dt.en}</option>)}
                            </select>
                        </div>
                        <div className="form-group">
                            <label>{t('hr.documents.document_number')}</label>
                            <input className="form-input" value={form.document_number} onChange={e => setForm({ ...form, document_number: e.target.value })} />
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                            <div className="form-group">
                                <label>{t('hr.documents.issue_date')}</label>
                                <DateInput className="form-input" value={form.issue_date} onChange={e => setForm({ ...form, issue_date: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>{t('hr.documents.expiry_date')}</label>
                                <DateInput className="form-input" value={form.expiry_date} onChange={e => setForm({ ...form, expiry_date: e.target.value })} />
                            </div>
                        </div>
                        <div className="form-group">
                            <label>{t('hr.documents.notes')}</label>
                            <textarea className="form-input" rows="2" value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} />
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
                            <button className="btn btn-secondary" onClick={() => setShowModal(false)}>{t('hr.documents.cancel')}</button>
                            <button className="btn btn-primary" onClick={handleSave}>{t('hr.documents.save')}</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default EmployeeDocuments;
