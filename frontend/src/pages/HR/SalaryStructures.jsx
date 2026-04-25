import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { hrAdvancedAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import { formatNumber } from '../../utils/format';
import { Plus, Edit2, Trash2 } from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';

const SalaryStructures = () => {
    const { t } = useTranslation();
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
        } catch (e) { toastEmitter.emit(t('common.error'), 'error'); }
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
        } catch (e) { toastEmitter.emit(t('common.error'), 'error'); }
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
        } catch (e) { toastEmitter.emit(t('common.error'), 'error'); }
    };

    const handleDeleteStructure = async (id) => {
        if (!window.confirm(t('hr.salary_structures.are_you_sure'))) return;
        try {
            await hrAdvancedAPI.deleteSalaryStructure(id);
            fetchData();
        } catch (e) { toastEmitter.emit(t('common.error'), 'error'); }
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">{t('hr.salary_structures.salary_structures_components')}</h1>
                    <p className="workspace-subtitle">{t('hr.salary_structures.manage_salary_structures_and_components')}</p>
                </div>
            </div>

            {/* Tabs */}
            <div className="card" style={{ marginBottom: '1rem', padding: '0.5rem' }}>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button className={`btn ${activeTab === 'structures' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setActiveTab('structures')}>
                        {t('hr.salary_structures.structures')}
                    </button>
                    <button className={`btn ${activeTab === 'components' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setActiveTab('components')}>
                        {t('hr.salary_structures.components')}
                    </button>
                </div>
            </div>

            {activeTab === 'structures' && (
                <>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
                        <button className="btn btn-primary" onClick={() => { setEditItem(null); setForm({ name: '', name_en: '', description: '' }); setShowStructureModal(true); }}>
                            <Plus size={16} /> {t('hr.salary_structures.new_structure')}
                        </button>
                    </div>
                    <div className="card">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>{t('hr.salary_structures.name')}</th>
                                    <th>{t('hr.salary_structures.name_en')}</th>
                                    <th>{t('hr.salary_structures.description')}</th>
                                    <th>{t('hr.salary_structures.status')}</th>
                                    <th>{t('hr.salary_structures.actions')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    <tr><td colSpan="6" style={{ textAlign: 'center', padding: '2rem' }}>{t('hr.salary_structures.loading')}</td></tr>
                                ) : structures.length === 0 ? (
                                    <tr><td colSpan="6" style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>{t('hr.salary_structures.no_salary_structures')}</td></tr>
                                ) : structures.map((s, i) => (
                                    <tr key={s.id}>
                                        <td>{i + 1}</td>
                                        <td style={{ fontWeight: 600 }}>{s.name}</td>
                                        <td>{s.name_en}</td>
                                        <td>{s.description || '-'}</td>
                                        <td><span className={`badge ${s.is_active ? 'badge-success' : 'badge-danger'}`}>{s.is_active ? (t('hr.salary_structures.active')) : (t('hr.salary_structures.inactive'))}</span></td>
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
                            <Plus size={16} /> {t('hr.salary_structures.new_component')}
                        </button>
                    </div>
                    <div className="card">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>{t('hr.salary_structures.name')}</th>
                                    <th>{t('hr.salary_structures.type')}</th>
                                    <th>{t('hr.salary_structures.calculation')}</th>
                                    <th>{t('hr.salary_structures.default_amount')}</th>
                                    <th>{t('hr.salary_structures.taxable')}</th>
                                    <th>{t('hr.salary_structures.actions')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    <tr><td colSpan="7" style={{ textAlign: 'center', padding: '2rem' }}>{t('hr.salary_structures.loading')}</td></tr>
                                ) : components.length === 0 ? (
                                    <tr><td colSpan="7" style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>{t('hr.salary_structures.no_components')}</td></tr>
                                ) : components.map((c, i) => (
                                    <tr key={c.id}>
                                        <td>{i + 1}</td>
                                        <td style={{ fontWeight: 600 }}>{c.name}</td>
                                        <td><span className={`badge ${c.type === 'earning' ? 'badge-success' : 'badge-danger'}`}>{c.type === 'earning' ? (t('hr.salary_structures.earning')) : (t('hr.salary_structures.deduction'))}</span></td>
                                        <td>{c.calculation_type === 'fixed' ? (t('hr.salary_structures.fixed')) : c.calculation_type === 'percentage' ? (t('hr.salary_structures.percentage')) : (t('hr.salary_structures.formula'))}</td>
                                        <td>{formatNumber(c.default_amount) || 0}</td>
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
                        <h2 className="modal-title">{editItem ? (t('hr.salary_structures.edit_structure')) : (t('hr.salary_structures.new_structure'))}</h2>
                        <div className="form-group">
                            <label>{t('hr.salary_structures.name_ar')}</label>
                            <input className="form-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
                        </div>
                        <div className="form-group">
                            <label>{t('hr.salary_structures.name_en_2')}</label>
                            <input className="form-input" value={form.name_en} onChange={e => setForm({ ...form, name_en: e.target.value })} />
                        </div>
                        <div className="form-group">
                            <label>{t('hr.salary_structures.description')}</label>
                            <textarea className="form-input" rows="3" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
                            <button className="btn btn-secondary" onClick={() => setShowStructureModal(false)}>{t('hr.salary_structures.cancel')}</button>
                            <button className="btn btn-primary" onClick={handleSaveStructure}>{t('hr.salary_structures.save')}</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Component Modal */}
            {showComponentModal && (
                <div className="modal-overlay" onClick={() => setShowComponentModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
                        <h2 className="modal-title">{editItem ? (t('hr.salary_structures.edit_component')) : (t('hr.salary_structures.new_component'))}</h2>
                        <div className="form-group">
                            <label>{t('hr.salary_structures.name')}</label>
                            <input className="form-input" value={compForm.name} onChange={e => setCompForm({ ...compForm, name: e.target.value })} />
                        </div>
                        <div className="form-group">
                            <label>{t('hr.salary_structures.name_en_3')}</label>
                            <input className="form-input" value={compForm.name_en} onChange={e => setCompForm({ ...compForm, name_en: e.target.value })} />
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                            <div className="form-group">
                                <label>{t('hr.salary_structures.type')}</label>
                                <select className="form-input" value={compForm.type} onChange={e => setCompForm({ ...compForm, type: e.target.value })}>
                                    <option value="earning">{t('hr.salary_structures.earning')}</option>
                                    <option value="deduction">{t('hr.salary_structures.deduction')}</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>{t('hr.salary_structures.calculation')}</label>
                                <select className="form-input" value={compForm.calculation_type} onChange={e => setCompForm({ ...compForm, calculation_type: e.target.value })}>
                                    <option value="fixed">{t('hr.salary_structures.fixed')}</option>
                                    <option value="percentage">{t('hr.salary_structures.percentage')}</option>
                                    <option value="formula">{t('hr.salary_structures.formula')}</option>
                                </select>
                            </div>
                        </div>
                        <div className="form-group">
                            <label>{t('hr.salary_structures.default_amount')}</label>
                            <input type="number" className="form-input" value={compForm.default_amount} onChange={e => setCompForm({ ...compForm, default_amount: e.target.value })} />
                        </div>
                        <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <input type="checkbox" checked={compForm.is_taxable} onChange={e => setCompForm({ ...compForm, is_taxable: e.target.checked })} />
                            <label style={{ margin: 0 }}>{t('hr.salary_structures.taxable')}</label>
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
                            <button className="btn btn-secondary" onClick={() => setShowComponentModal(false)}>{t('hr.salary_structures.cancel')}</button>
                            <button className="btn btn-primary" onClick={handleSaveComponent}>{t('hr.salary_structures.save')}</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SalaryStructures;
