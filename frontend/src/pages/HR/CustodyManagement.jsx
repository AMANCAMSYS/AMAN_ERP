import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { hrAdvancedAPI, hrAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import { Plus, Edit2, RotateCcw } from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';

import DateInput from '../../components/common/DateInput';
import BackButton from '../../components/common/BackButton';
const CustodyManagement = () => {
    const { t, i18n } = useTranslation();
    const [items, setItems] = useState([]);
    const [employees, setEmployees] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [showReturnModal, setShowReturnModal] = useState(false);
    const [editItem, setEditItem] = useState(null);
    const [returnItem, setReturnItem] = useState(null);
    const [form, setForm] = useState({ employee_id: '', item_name: '', item_type: 'laptop', serial_number: '', assigned_date: '', notes: '' });
    const [returnForm, setReturnForm] = useState({ return_notes: '', condition: 'good' });

    const itemTypes = [
        { value: 'laptop', ar: 'لابتوب', en: 'Laptop' },
        { value: 'mobile', ar: 'جوال', en: 'Mobile' },
        { value: 'car', ar: 'سيارة', en: 'Car' },
        { value: 'key', ar: 'مفتاح', en: 'Key' },
        { value: 'card', ar: 'بطاقة', en: 'Card' },
        { value: 'tool', ar: 'أداة', en: 'Tool' },
        { value: 'other', ar: 'أخرى', en: 'Other' }
    ];

    const fetchData = async () => {
        setLoading(true);
        try {
            const [cRes, empRes] = await Promise.all([
                hrAdvancedAPI.listCustody(),
                hrAPI.listEmployees({ limit: 200 })
            ]);
            setItems(cRes.data || []);
            setEmployees(empRes.data?.items || empRes.data || []);
        } catch (e) { toastEmitter.emit(t('common.error'), 'error'); }
        setLoading(false);
    };

    useEffect(() => { fetchData(); }, []);

    const handleSave = async () => {
        try {
            const payload = { ...form, employee_id: parseInt(form.employee_id) };
            if (editItem) {
                await hrAdvancedAPI.updateCustody(editItem.id, payload);
            } else {
                await hrAdvancedAPI.createCustody(payload);
            }
            setShowModal(false); setEditItem(null);
            setForm({ employee_id: '', item_name: '', item_type: 'laptop', serial_number: '', assigned_date: '', notes: '' });
            fetchData();
        } catch (e) { toastEmitter.emit(t('common.error'), 'error'); }
    };

    const handleReturn = async () => {
        try {
            await hrAdvancedAPI.returnCustody(returnItem.id, returnForm);
            setShowReturnModal(false); setReturnItem(null);
            fetchData();
        } catch (e) { toastEmitter.emit(t('common.error'), 'error'); }
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">{t('hr.custody.custody_management')}</h1>
                    <p className="workspace-subtitle">{t('hr.custody.track_employee_custody_items')}</p>
                </div>
                <button className="btn btn-primary" onClick={() => { setEditItem(null); setForm({ employee_id: '', item_name: '', item_type: 'laptop', serial_number: '', assigned_date: '', notes: '' }); setShowModal(true); }}>
                    <Plus size={16} /> {t('hr.custody.new_custody')}
                </button>
            </div>

            {/* Summary cards */}
            <div className="metrics-grid" style={{ marginBottom: '1rem' }}>
                <div className="metric-card">
                    <div className="metric-label">{t('hr.custody.total_items')}</div>
                    <div className="metric-value" style={{ color: '#2563eb' }}>{items.length}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('hr.custody.active')}</div>
                    <div className="metric-value" style={{ color: '#16a34a' }}>{items.filter(i => i.status === 'assigned' || !i.return_date).length}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('hr.custody.returned')}</div>
                    <div className="metric-value" style={{ color: '#6b7280' }}>{items.filter(i => i.status === 'returned' || i.return_date).length}</div>
                </div>
            </div>

            <div className="card">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>{t('hr.custody.employee')}</th>
                            <th>{t('hr.custody.item')}</th>
                            <th>{t('hr.custody.type')}</th>
                            <th>{t('hr.custody.serial')}</th>
                            <th>{t('hr.custody.assigned')}</th>
                            <th>{t('hr.custody.status')}</th>
                            <th>{t('hr.custody.actions')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan="8" style={{ textAlign: 'center', padding: '2rem' }}>{t('hr.custody.loading')}</td></tr>
                        ) : items.length === 0 ? (
                            <tr><td colSpan="8" style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>{t('hr.custody.no_custody_items')}</td></tr>
                        ) : items.map((item, i) => (
                            <tr key={item.id}>
                                <td>{i + 1}</td>
                                <td style={{ fontWeight: 600 }}>{item.employee_name || `#${item.employee_id}`}</td>
                                <td>{item.item_name}</td>
                                <td>{itemTypes.find(it => it.value === item.item_type)?.[t('hr.custody.en')] || item.item_type}</td>
                                <td>{item.serial_number || '-'}</td>
                                <td>{item.assigned_date || '-'}</td>
                                <td>
                                    <span className={`badge ${item.status === 'returned' || item.return_date ? 'badge-success' : 'badge-warning'}`}>
                                        {item.status === 'returned' || item.return_date ? (t('hr.custody.returned')) : (t('hr.custody.assigned_2'))}
                                    </span>
                                </td>
                                <td>
                                    <div style={{ display: 'flex', gap: '0.25rem' }}>
                                        {!item.return_date && item.status !== 'returned' && (
                                            <button className="btn btn-sm btn-success" onClick={() => { setReturnItem(item); setReturnForm({ return_notes: '', condition: 'good' }); setShowReturnModal(true); }} title={t('hr.custody.return')}>
                                                <RotateCcw size={14} />
                                            </button>
                                        )}
                                        <button className="btn btn-sm btn-secondary" onClick={() => { setEditItem(item); setForm({ employee_id: item.employee_id, item_name: item.item_name || '', item_type: item.item_type || 'laptop', serial_number: item.serial_number || '', assigned_date: item.assigned_date || '', notes: item.notes || '' }); setShowModal(true); }}><Edit2 size={14} /></button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Custody modal */}
            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
                        <h2 className="modal-title">{editItem ? (t('hr.custody.edit_custody')) : (t('hr.custody.new_custody'))}</h2>
                        <div className="form-group">
                            <label>{t('hr.custody.employee')}</label>
                            <select className="form-input" value={form.employee_id} onChange={e => setForm({ ...form, employee_id: e.target.value })}>
                                <option value="">{t('hr.custody.select')}</option>
                                {employees.map(emp => <option key={emp.id} value={emp.id}>{emp.name || emp.full_name}</option>)}
                            </select>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '0.75rem' }}>
                            <div className="form-group">
                                <label>{t('hr.custody.item_name')}</label>
                                <input className="form-input" value={form.item_name} onChange={e => setForm({ ...form, item_name: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>{t('hr.custody.type')}</label>
                                <select className="form-input" value={form.item_type} onChange={e => setForm({ ...form, item_type: e.target.value })}>
                                    {itemTypes.map(it => <option key={it.value} value={it.value}>{isRTL ? it.ar : it.en}</option>)}
                                </select>
                            </div>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                            <div className="form-group">
                                <label>{t('hr.custody.serial_number')}</label>
                                <input className="form-input" value={form.serial_number} onChange={e => setForm({ ...form, serial_number: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>{t('hr.custody.assigned_date')}</label>
                                <DateInput className="form-input" value={form.assigned_date} onChange={e => setForm({ ...form, assigned_date: e.target.value })} />
                            </div>
                        </div>
                        <div className="form-group">
                            <label>{t('hr.custody.notes')}</label>
                            <textarea className="form-input" rows="2" value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} />
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
                            <button className="btn btn-secondary" onClick={() => setShowModal(false)}>{t('hr.custody.cancel')}</button>
                            <button className="btn btn-primary" onClick={handleSave}>{t('hr.custody.save')}</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Return modal */}
            {showReturnModal && (
                <div className="modal-overlay" onClick={() => setShowReturnModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 400 }}>
                        <h2 className="modal-title">{t('hr.custody.return_custody')}</h2>
                        <p style={{ color: '#666', marginBottom: '1rem' }}>{t('hr.returning_item', { name: returnItem?.item_name })}</p>
                        <div className="form-group">
                            <label>{t('hr.custody.condition')}</label>
                            <select className="form-input" value={returnForm.condition} onChange={e => setReturnForm({ ...returnForm, condition: e.target.value })}>
                                <option value="good">{t('hr.custody.good')}</option>
                                <option value="damaged">{t('hr.custody.damaged')}</option>
                                <option value="needs_repair">{t('hr.custody.needs_repair')}</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label>{t('hr.custody.return_notes')}</label>
                            <textarea className="form-input" rows="2" value={returnForm.return_notes} onChange={e => setReturnForm({ ...returnForm, return_notes: e.target.value })} />
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
                            <button className="btn btn-secondary" onClick={() => setShowReturnModal(false)}>{t('hr.custody.cancel')}</button>
                            <button className="btn btn-success" onClick={handleReturn}>{t('hr.custody.confirm_return')}</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CustodyManagement;
