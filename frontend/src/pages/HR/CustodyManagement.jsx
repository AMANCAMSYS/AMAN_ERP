import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { hrAdvancedAPI, hrAPI } from '../../utils/api';
import { Plus, Edit2, RotateCcw, Package } from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';

import DateInput from '../../components/common/DateInput';
const CustodyManagement = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
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
        } catch (e) { console.error(e); }
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
        } catch (e) { console.error(e); }
    };

    const handleReturn = async () => {
        try {
            await hrAdvancedAPI.returnCustody(returnItem.id, returnForm);
            setShowReturnModal(false); setReturnItem(null);
            fetchData();
        } catch (e) { console.error(e); }
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div className="header-title">
                    <h1 className="workspace-title">{isRTL ? 'إدارة العهد' : 'Custody Management'}</h1>
                    <p className="workspace-subtitle">{isRTL ? 'تتبع عهد الموظفين (أجهزة/مفاتيح/سيارات)' : 'Track employee custody items'}</p>
                </div>
                <button className="btn btn-primary" onClick={() => { setEditItem(null); setForm({ employee_id: '', item_name: '', item_type: 'laptop', serial_number: '', assigned_date: '', notes: '' }); setShowModal(true); }}>
                    <Plus size={16} /> {isRTL ? 'عهدة جديدة' : 'New Custody'}
                </button>
            </div>

            {/* Summary cards */}
            <div className="metrics-grid" style={{ marginBottom: '1rem' }}>
                <div className="metric-card">
                    <div className="metric-label">{isRTL ? 'إجمالي العهد' : 'Total Items'}</div>
                    <div className="metric-value" style={{ color: '#2563eb' }}>{items.length}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{isRTL ? 'عهد فعالة' : 'Active'}</div>
                    <div className="metric-value" style={{ color: '#16a34a' }}>{items.filter(i => i.status === 'assigned' || !i.return_date).length}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{isRTL ? 'تم الإرجاع' : 'Returned'}</div>
                    <div className="metric-value" style={{ color: '#6b7280' }}>{items.filter(i => i.status === 'returned' || i.return_date).length}</div>
                </div>
            </div>

            <div className="card">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>{isRTL ? 'الموظف' : 'Employee'}</th>
                            <th>{isRTL ? 'الصنف' : 'Item'}</th>
                            <th>{isRTL ? 'النوع' : 'Type'}</th>
                            <th>{isRTL ? 'الرقم التسلسلي' : 'Serial'}</th>
                            <th>{isRTL ? 'تاريخ التسليم' : 'Assigned'}</th>
                            <th>{isRTL ? 'الحالة' : 'Status'}</th>
                            <th>{isRTL ? 'إجراءات' : 'Actions'}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan="8" style={{ textAlign: 'center', padding: '2rem' }}>{isRTL ? 'جاري التحميل...' : 'Loading...'}</td></tr>
                        ) : items.length === 0 ? (
                            <tr><td colSpan="8" style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>{isRTL ? 'لا توجد عهد' : 'No custody items'}</td></tr>
                        ) : items.map((item, i) => (
                            <tr key={item.id}>
                                <td>{i + 1}</td>
                                <td style={{ fontWeight: 600 }}>{item.employee_name || `#${item.employee_id}`}</td>
                                <td>{item.item_name}</td>
                                <td>{itemTypes.find(it => it.value === item.item_type)?.[isRTL ? 'ar' : 'en'] || item.item_type}</td>
                                <td>{item.serial_number || '-'}</td>
                                <td>{item.assigned_date || '-'}</td>
                                <td>
                                    <span className={`badge ${item.status === 'returned' || item.return_date ? 'badge-success' : 'badge-warning'}`}>
                                        {item.status === 'returned' || item.return_date ? (isRTL ? 'تم الإرجاع' : 'Returned') : (isRTL ? 'عند الموظف' : 'Assigned')}
                                    </span>
                                </td>
                                <td>
                                    <div style={{ display: 'flex', gap: '0.25rem' }}>
                                        {!item.return_date && item.status !== 'returned' && (
                                            <button className="btn btn-sm btn-success" onClick={() => { setReturnItem(item); setReturnForm({ return_notes: '', condition: 'good' }); setShowReturnModal(true); }} title={isRTL ? 'إرجاع' : 'Return'}>
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
                        <h2 className="modal-title">{editItem ? (isRTL ? 'تعديل عهدة' : 'Edit Custody') : (isRTL ? 'عهدة جديدة' : 'New Custody')}</h2>
                        <div className="form-group">
                            <label>{isRTL ? 'الموظف' : 'Employee'}</label>
                            <select className="form-input" value={form.employee_id} onChange={e => setForm({ ...form, employee_id: e.target.value })}>
                                <option value="">{isRTL ? '-- اختر --' : '-- Select --'}</option>
                                {employees.map(emp => <option key={emp.id} value={emp.id}>{emp.name || emp.full_name}</option>)}
                            </select>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '0.75rem' }}>
                            <div className="form-group">
                                <label>{isRTL ? 'اسم الصنف' : 'Item Name'}</label>
                                <input className="form-input" value={form.item_name} onChange={e => setForm({ ...form, item_name: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>{isRTL ? 'النوع' : 'Type'}</label>
                                <select className="form-input" value={form.item_type} onChange={e => setForm({ ...form, item_type: e.target.value })}>
                                    {itemTypes.map(it => <option key={it.value} value={it.value}>{isRTL ? it.ar : it.en}</option>)}
                                </select>
                            </div>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                            <div className="form-group">
                                <label>{isRTL ? 'الرقم التسلسلي' : 'Serial Number'}</label>
                                <input className="form-input" value={form.serial_number} onChange={e => setForm({ ...form, serial_number: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>{isRTL ? 'تاريخ التسليم' : 'Assigned Date'}</label>
                                <DateInput className="form-input" value={form.assigned_date} onChange={e => setForm({ ...form, assigned_date: e.target.value })} />
                            </div>
                        </div>
                        <div className="form-group">
                            <label>{isRTL ? 'ملاحظات' : 'Notes'}</label>
                            <textarea className="form-input" rows="2" value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} />
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
                            <button className="btn btn-secondary" onClick={() => setShowModal(false)}>{isRTL ? 'إلغاء' : 'Cancel'}</button>
                            <button className="btn btn-primary" onClick={handleSave}>{isRTL ? 'حفظ' : 'Save'}</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Return modal */}
            {showReturnModal && (
                <div className="modal-overlay" onClick={() => setShowReturnModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 400 }}>
                        <h2 className="modal-title">{isRTL ? 'إرجاع العهدة' : 'Return Custody'}</h2>
                        <p style={{ color: '#666', marginBottom: '1rem' }}>{isRTL ? `إرجاع: ${returnItem?.item_name}` : `Returning: ${returnItem?.item_name}`}</p>
                        <div className="form-group">
                            <label>{isRTL ? 'حالة الصنف' : 'Condition'}</label>
                            <select className="form-input" value={returnForm.condition} onChange={e => setReturnForm({ ...returnForm, condition: e.target.value })}>
                                <option value="good">{isRTL ? 'جيد' : 'Good'}</option>
                                <option value="damaged">{isRTL ? 'تالف' : 'Damaged'}</option>
                                <option value="needs_repair">{isRTL ? 'يحتاج إصلاح' : 'Needs Repair'}</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label>{isRTL ? 'ملاحظات الإرجاع' : 'Return Notes'}</label>
                            <textarea className="form-input" rows="2" value={returnForm.return_notes} onChange={e => setReturnForm({ ...returnForm, return_notes: e.target.value })} />
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
                            <button className="btn btn-secondary" onClick={() => setShowReturnModal(false)}>{isRTL ? 'إلغاء' : 'Cancel'}</button>
                            <button className="btn btn-success" onClick={handleReturn}>{isRTL ? 'تأكيد الإرجاع' : 'Confirm Return'}</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CustodyManagement;
