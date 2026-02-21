import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { hrAdvancedAPI, hrAPI } from '../../utils/api';
import { hasPermission } from '../../utils/auth';
import { Plus, Edit2, Trash2, DollarSign, Settings, ChevronDown, ChevronUp } from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';

const SalaryStructures = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const [structures, setStructures] = useState([]);
    const [components, setComponents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showStructureModal, setShowStructureModal] = useState(false);
    const [showComponentModal, setShowComponentModal] = useState(false);
    const [activeTab, setActiveTab] = useState('structures');
    const [editItem, setEditItem] = useState(null);
    const [form, setForm] = useState({ name: '', name_en: '', description: '' });
    const [compForm, setCompForm] = useState({ name: '', name_en: '', type: 'earning', calculation_type: 'fixed', default_amount: 0, is_taxable: true });

    const fetchData = async () => {
        setLoading(true);
        try {
            const [sRes, cRes] = await Promise.all([
                hrAdvancedAPI.listSalaryStructures(),
                hrAdvancedAPI.listSalaryComponents()
            ]);
            setStructures(sRes.data || []);
            setComponents(cRes.data || []);
        } catch (e) { console.error(e); }
        setLoading(false);
    };

    useEffect(() => { fetchData(); }, []);

    const handleSaveStructure = async () => {
        try {
            if (editItem) {
                await hrAdvancedAPI.updateSalaryStructure(editItem.id, form);
            } else {
                await hrAdvancedAPI.createSalaryStructure(form);
            }
            setShowStructureModal(false);
            setEditItem(null);
            setForm({ name: '', name_en: '', description: '' });
            fetchData();
        } catch (e) { console.error(e); }
    };

    const handleSaveComponent = async () => {
        try {
            if (editItem) {
                await hrAdvancedAPI.updateSalaryComponent(editItem.id, compForm);
            } else {
                await hrAdvancedAPI.createSalaryComponent(compForm);
            }
            setShowComponentModal(false);
            setEditItem(null);
            setCompForm({ name: '', name_en: '', type: 'earning', calculation_type: 'fixed', default_amount: 0, is_taxable: true });
            fetchData();
        } catch (e) { console.error(e); }
    };

    const handleDeleteStructure = async (id) => {
        if (!window.confirm(isRTL ? 'هل أنت متأكد من الحذف؟' : 'Are you sure?')) return;
        try {
            await hrAdvancedAPI.deleteSalaryStructure(id);
            fetchData();
        } catch (e) { console.error(e); }
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div className="header-title">
                    <h1 className="workspace-title">{isRTL ? 'هياكل الرواتب والمكونات' : 'Salary Structures & Components'}</h1>
                    <p className="workspace-subtitle">{isRTL ? 'إدارة هياكل ومكونات الرواتب' : 'Manage salary structures and components'}</p>
                </div>
            </div>

            {/* Tabs */}
            <div className="card" style={{ marginBottom: '1rem', padding: '0.5rem' }}>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button className={`btn ${activeTab === 'structures' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setActiveTab('structures')}>
                        {isRTL ? '📋 هياكل الرواتب' : '📋 Structures'}
                    </button>
                    <button className={`btn ${activeTab === 'components' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setActiveTab('components')}>
                        {isRTL ? '🧩 المكونات' : '🧩 Components'}
                    </button>
                </div>
            </div>

            {activeTab === 'structures' && (
                <>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
                        <button className="btn btn-primary" onClick={() => { setEditItem(null); setForm({ name: '', name_en: '', description: '' }); setShowStructureModal(true); }}>
                            <Plus size={16} /> {isRTL ? 'هيكل جديد' : 'New Structure'}
                        </button>
                    </div>
                    <div className="card">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>{isRTL ? 'الاسم' : 'Name'}</th>
                                    <th>{isRTL ? 'الاسم (EN)' : 'Name (EN)'}</th>
                                    <th>{isRTL ? 'الوصف' : 'Description'}</th>
                                    <th>{isRTL ? 'الحالة' : 'Status'}</th>
                                    <th>{isRTL ? 'إجراءات' : 'Actions'}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    <tr><td colSpan="6" style={{ textAlign: 'center', padding: '2rem' }}>{isRTL ? 'جاري التحميل...' : 'Loading...'}</td></tr>
                                ) : structures.length === 0 ? (
                                    <tr><td colSpan="6" style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>{isRTL ? 'لا توجد هياكل رواتب' : 'No salary structures'}</td></tr>
                                ) : structures.map((s, i) => (
                                    <tr key={s.id}>
                                        <td>{i + 1}</td>
                                        <td style={{ fontWeight: 600 }}>{s.name}</td>
                                        <td>{s.name_en}</td>
                                        <td>{s.description || '-'}</td>
                                        <td><span className={`badge ${s.is_active ? 'badge-success' : 'badge-danger'}`}>{s.is_active ? (isRTL ? 'نشط' : 'Active') : (isRTL ? 'غير نشط' : 'Inactive')}</span></td>
                                        <td>
                                            <div style={{ display: 'flex', gap: '0.25rem' }}>
                                                <button className="btn btn-sm btn-secondary" onClick={() => { setEditItem(s); setForm({ name: s.name, name_en: s.name_en || '', description: s.description || '' }); setShowStructureModal(true); }}><Edit2 size={14} /></button>
                                                <button className="btn btn-sm btn-danger" onClick={() => handleDeleteStructure(s.id)}><Trash2 size={14} /></button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </>
            )}

            {activeTab === 'components' && (
                <>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
                        <button className="btn btn-primary" onClick={() => { setEditItem(null); setCompForm({ name: '', name_en: '', type: 'earning', calculation_type: 'fixed', default_amount: 0, is_taxable: true }); setShowComponentModal(true); }}>
                            <Plus size={16} /> {isRTL ? 'مكون جديد' : 'New Component'}
                        </button>
                    </div>
                    <div className="card">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>{isRTL ? 'الاسم' : 'Name'}</th>
                                    <th>{isRTL ? 'النوع' : 'Type'}</th>
                                    <th>{isRTL ? 'طريقة الحساب' : 'Calculation'}</th>
                                    <th>{isRTL ? 'المبلغ الافتراضي' : 'Default Amount'}</th>
                                    <th>{isRTL ? 'خاضع للضريبة' : 'Taxable'}</th>
                                    <th>{isRTL ? 'إجراءات' : 'Actions'}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    <tr><td colSpan="7" style={{ textAlign: 'center', padding: '2rem' }}>{isRTL ? 'جاري التحميل...' : 'Loading...'}</td></tr>
                                ) : components.length === 0 ? (
                                    <tr><td colSpan="7" style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>{isRTL ? 'لا توجد مكونات' : 'No components'}</td></tr>
                                ) : components.map((c, i) => (
                                    <tr key={c.id}>
                                        <td>{i + 1}</td>
                                        <td style={{ fontWeight: 600 }}>{c.name}</td>
                                        <td><span className={`badge ${c.type === 'earning' ? 'badge-success' : 'badge-danger'}`}>{c.type === 'earning' ? (isRTL ? 'علاوة' : 'Earning') : (isRTL ? 'استقطاع' : 'Deduction')}</span></td>
                                        <td>{c.calculation_type === 'fixed' ? (isRTL ? 'ثابت' : 'Fixed') : c.calculation_type === 'percentage' ? (isRTL ? 'نسبة' : '%') : (isRTL ? 'صيغة' : 'Formula')}</td>
                                        <td>{c.default_amount?.toLocaleString() || 0}</td>
                                        <td>{c.is_taxable ? '✅' : '❌'}</td>
                                        <td>
                                            <button className="btn btn-sm btn-secondary" onClick={() => { setEditItem(c); setCompForm({ name: c.name, name_en: c.name_en || '', type: c.type, calculation_type: c.calculation_type, default_amount: c.default_amount || 0, is_taxable: c.is_taxable }); setShowComponentModal(true); }}><Edit2 size={14} /></button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </>
            )}

            {/* Structure Modal */}
            {showStructureModal && (
                <div className="modal-overlay" onClick={() => setShowStructureModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
                        <h2 className="modal-title">{editItem ? (isRTL ? 'تعديل هيكل' : 'Edit Structure') : (isRTL ? 'هيكل جديد' : 'New Structure')}</h2>
                        <div className="form-group">
                            <label>{isRTL ? 'الاسم بالعربي' : 'Name (AR)'}</label>
                            <input className="form-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
                        </div>
                        <div className="form-group">
                            <label>{isRTL ? 'الاسم بالإنجليزي' : 'Name (EN)'}</label>
                            <input className="form-input" value={form.name_en} onChange={e => setForm({ ...form, name_en: e.target.value })} />
                        </div>
                        <div className="form-group">
                            <label>{isRTL ? 'الوصف' : 'Description'}</label>
                            <textarea className="form-input" rows="3" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
                            <button className="btn btn-secondary" onClick={() => setShowStructureModal(false)}>{isRTL ? 'إلغاء' : 'Cancel'}</button>
                            <button className="btn btn-primary" onClick={handleSaveStructure}>{isRTL ? 'حفظ' : 'Save'}</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Component Modal */}
            {showComponentModal && (
                <div className="modal-overlay" onClick={() => setShowComponentModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
                        <h2 className="modal-title">{editItem ? (isRTL ? 'تعديل مكون' : 'Edit Component') : (isRTL ? 'مكون جديد' : 'New Component')}</h2>
                        <div className="form-group">
                            <label>{isRTL ? 'الاسم' : 'Name'}</label>
                            <input className="form-input" value={compForm.name} onChange={e => setCompForm({ ...compForm, name: e.target.value })} />
                        </div>
                        <div className="form-group">
                            <label>{isRTL ? 'الاسم EN' : 'Name EN'}</label>
                            <input className="form-input" value={compForm.name_en} onChange={e => setCompForm({ ...compForm, name_en: e.target.value })} />
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                            <div className="form-group">
                                <label>{isRTL ? 'النوع' : 'Type'}</label>
                                <select className="form-input" value={compForm.type} onChange={e => setCompForm({ ...compForm, type: e.target.value })}>
                                    <option value="earning">{isRTL ? 'علاوة' : 'Earning'}</option>
                                    <option value="deduction">{isRTL ? 'استقطاع' : 'Deduction'}</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>{isRTL ? 'طريقة الحساب' : 'Calculation'}</label>
                                <select className="form-input" value={compForm.calculation_type} onChange={e => setCompForm({ ...compForm, calculation_type: e.target.value })}>
                                    <option value="fixed">{isRTL ? 'ثابت' : 'Fixed'}</option>
                                    <option value="percentage">{isRTL ? 'نسبة مئوية' : 'Percentage'}</option>
                                    <option value="formula">{isRTL ? 'صيغة' : 'Formula'}</option>
                                </select>
                            </div>
                        </div>
                        <div className="form-group">
                            <label>{isRTL ? 'المبلغ الافتراضي' : 'Default Amount'}</label>
                            <input type="number" className="form-input" value={compForm.default_amount} onChange={e => setCompForm({ ...compForm, default_amount: parseFloat(e.target.value) || 0 })} />
                        </div>
                        <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <input type="checkbox" checked={compForm.is_taxable} onChange={e => setCompForm({ ...compForm, is_taxable: e.target.checked })} />
                            <label style={{ margin: 0 }}>{isRTL ? 'خاضع للضريبة' : 'Taxable'}</label>
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
                            <button className="btn btn-secondary" onClick={() => setShowComponentModal(false)}>{isRTL ? 'إلغاء' : 'Cancel'}</button>
                            <button className="btn btn-primary" onClick={handleSaveComponent}>{isRTL ? 'حفظ' : 'Save'}</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SalaryStructures;
