import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { hrAdvancedAPI } from '../../utils/api';
import { Save, Calculator, Shield } from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';

const GOSISettings = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const [settings, setSettings] = useState(null);
    const [calculations, setCalculations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('settings');
    const [form, setForm] = useState({
        employee_share_percentage: 9.75,
        employer_share_percentage: 11.75,
        occupational_hazard_percentage: 2.0,
        max_insurable_salary: 45000,
        is_active: true
    });

    const fetchData = async () => {
        setLoading(true);
        try {
            const res = await hrAdvancedAPI.getGOSISettings();
            const data = Array.isArray(res.data) ? res.data : [res.data];
            if (data.length > 0 && data[0]) {
                setSettings(data[0]);
                setForm({
                    employee_share_percentage: data[0].employee_share_percentage || 9.75,
                    employer_share_percentage: data[0].employer_share_percentage || 11.75,
                    occupational_hazard_percentage: data[0].occupational_hazard_percentage || 2.0,
                    max_insurable_salary: data[0].max_insurable_salary || 45000,
                    is_active: data[0].is_active !== false
                });
            }
        } catch (e) { console.error(e); }
        setLoading(false);
    };

    const fetchCalc = async () => {
        try {
            const res = await hrAdvancedAPI.calculateGOSI();
            setCalculations(res.data || []);
        } catch (e) { console.error(e); }
    };

    useEffect(() => { fetchData(); }, []);

    const handleSave = async () => {
        try {
            await hrAdvancedAPI.saveGOSISettings(form);
            fetchData();
        } catch (e) { console.error(e); }
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div className="header-title">
                    <h1 className="workspace-title">{isRTL ? 'التأمينات الاجتماعية (GOSI)' : 'Social Insurance (GOSI)'}</h1>
                    <p className="workspace-subtitle">{isRTL ? 'إعدادات وحسابات التأمينات الاجتماعية' : 'GOSI settings and calculations'}</p>
                </div>
            </div>

            {/* Tabs */}
            <div className="card" style={{ marginBottom: '1rem', padding: '0.5rem' }}>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button className={`btn ${activeTab === 'settings' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setActiveTab('settings')}>
                        <Shield size={16} /> {isRTL ? 'الإعدادات' : 'Settings'}
                    </button>
                    <button className={`btn ${activeTab === 'calc' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => { setActiveTab('calc'); fetchCalc(); }}>
                        <Calculator size={16} /> {isRTL ? 'الحسابات' : 'Calculations'}
                    </button>
                </div>
            </div>

            {activeTab === 'settings' && (
                <div className="card" style={{ maxWidth: 600 }}>
                    <h3 style={{ marginBottom: '1.5rem', color: '#1a1a2e' }}>{isRTL ? 'نسب الاشتراك' : 'Contribution Rates'}</h3>
                    <div className="form-group">
                        <label>{isRTL ? 'نسبة حصة الموظف (%)' : 'Employee Share (%)'}</label>
                        <input type="number" step="0.25" className="form-input" value={form.employee_share_percentage} onChange={e => setForm({ ...form, employee_share_percentage: parseFloat(e.target.value) })} />
                    </div>
                    <div className="form-group">
                        <label>{isRTL ? 'نسبة حصة صاحب العمل (%)' : 'Employer Share (%)'}</label>
                        <input type="number" step="0.25" className="form-input" value={form.employer_share_percentage} onChange={e => setForm({ ...form, employer_share_percentage: parseFloat(e.target.value) })} />
                    </div>
                    <div className="form-group">
                        <label>{isRTL ? 'نسبة خطر المهنة (%)' : 'Occupational Hazard (%)'}</label>
                        <input type="number" step="0.25" className="form-input" value={form.occupational_hazard_percentage} onChange={e => setForm({ ...form, occupational_hazard_percentage: parseFloat(e.target.value) })} />
                    </div>
                    <div className="form-group">
                        <label>{isRTL ? 'الحد الأقصى للراتب المؤمن عليه' : 'Max Insurable Salary'}</label>
                        <input type="number" className="form-input" value={form.max_insurable_salary} onChange={e => setForm({ ...form, max_insurable_salary: parseFloat(e.target.value) })} />
                    </div>
                    <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <input type="checkbox" checked={form.is_active} onChange={e => setForm({ ...form, is_active: e.target.checked })} />
                        <label style={{ margin: 0 }}>{isRTL ? 'مفعّل' : 'Active'}</label>
                    </div>

                    {/* Summary card */}
                    <div style={{ background: '#f0f4ff', borderRadius: 8, padding: '1rem', marginTop: '1rem', marginBottom: '1rem' }}>
                        <p style={{ margin: '0.25rem 0', fontSize: '0.9rem' }}>
                            <strong>{isRTL ? 'إجمالي على الموظف:' : 'Total Employee:'}</strong> {form.employee_share_percentage}%
                        </p>
                        <p style={{ margin: '0.25rem 0', fontSize: '0.9rem' }}>
                            <strong>{isRTL ? 'إجمالي على صاحب العمل:' : 'Total Employer:'}</strong> {(form.employer_share_percentage + form.occupational_hazard_percentage).toFixed(2)}%
                        </p>
                    </div>

                    <button className="btn btn-primary" onClick={handleSave} style={{ width: '100%' }}>
                        <Save size={16} /> {isRTL ? 'حفظ الإعدادات' : 'Save Settings'}
                    </button>
                </div>
            )}

            {activeTab === 'calc' && (
                <div className="card">
                    <h3 style={{ marginBottom: '1rem' }}>{isRTL ? 'حسابات GOSI الشهرية' : 'Monthly GOSI Calculations'}</h3>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>{isRTL ? 'الموظف' : 'Employee'}</th>
                                <th>{isRTL ? 'الراتب الأساسي' : 'Basic Salary'}</th>
                                <th>{isRTL ? 'حصة الموظف' : 'Employee Share'}</th>
                                <th>{isRTL ? 'حصة صاحب العمل' : 'Employer Share'}</th>
                                <th>{isRTL ? 'الإجمالي' : 'Total'}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {calculations.length === 0 ? (
                                <tr><td colSpan="5" style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>{isRTL ? 'لا توجد بيانات' : 'No data'}</td></tr>
                            ) : calculations.map((c, i) => (
                                <tr key={i}>
                                    <td style={{ fontWeight: 600 }}>{c.employee_name || `#${c.employee_id}`}</td>
                                    <td>{c.basic_salary?.toLocaleString()}</td>
                                    <td>{c.employee_share?.toLocaleString()}</td>
                                    <td>{c.employer_share?.toLocaleString()}</td>
                                    <td style={{ fontWeight: 700 }}>{c.total?.toLocaleString()}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

export default GOSISettings;
