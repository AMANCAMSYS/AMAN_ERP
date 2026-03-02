import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { contractsAPI } from '../../utils/api';
import { useToast } from '../../context/ToastContext';
import { FileText, Plus, Save, X, BarChart3, Calendar, DollarSign, TrendingUp } from 'lucide-react';
import BackButton from '../../components/common/BackButton';
import '../../components/ModuleStyles.css';
import DateInput from '../../components/common/DateInput';

const ContractAmendments = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const { showToast } = useToast();
    const [activeTab, setActiveTab] = useState('amendments');
    const [contracts, setContracts] = useState([]);
    const [selectedContract, setSelectedContract] = useState('');
    const [amendments, setAmendments] = useState([]);
    const [kpis, setKpis] = useState(null);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [form, setForm] = useState({
        amendment_type: 'scope_change', description: '',
        old_value: '', new_value: '', effective_date: '', approved_by: ''
    });

    useEffect(() => { fetchContracts(); }, []);
    useEffect(() => { if (selectedContract) fetchData(); }, [selectedContract, activeTab]);

    const fetchContracts = async () => {
        try {
            const res = await contractsAPI.list();
            const list = res.data?.contracts || res.data || [];
            setContracts(list);
            if (list.length > 0) setSelectedContract(list[0].id);
        } catch (err) { console.error(err); }
    };

    const fetchData = async () => {
        try {
            setLoading(true);
            if (activeTab === 'amendments') {
                const res = await contractsAPI.listAmendments(selectedContract);
                setAmendments(res.data || []);
            } else {
                const res = await contractsAPI.getContractKPIs(selectedContract);
                setKpis(res.data);
            }
        } catch (err) { console.error(err); } finally { setLoading(false); }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await contractsAPI.createAmendment(selectedContract, form);
            showToast(isRTL ? 'تم إضافة التعديل' : 'Amendment added', 'success');
            setShowForm(false);
            setForm({ amendment_type: 'scope_change', description: '', old_value: '', new_value: '', effective_date: '', approved_by: '' });
            fetchData();
        } catch (err) { showToast(err.response?.data?.detail || 'Error', 'error'); }
    };

    const amendmentTypes = {
        scope_change: { label: isRTL ? 'تغيير النطاق' : 'Scope Change', color: '#1565c0' },
        price_adjustment: { label: isRTL ? 'تعديل السعر' : 'Price Adjustment', color: '#2e7d32' },
        term_extension: { label: isRTL ? 'تمديد المدة' : 'Term Extension', color: '#f57f17' },
        term_reduction: { label: isRTL ? 'تقليص المدة' : 'Term Reduction', color: '#e65100' },
        clause_modification: { label: isRTL ? 'تعديل بند' : 'Clause Modification', color: '#7b1fa2' },
        party_change: { label: isRTL ? 'تغيير طرف' : 'Party Change', color: '#00838f' },
        termination: { label: isRTL ? 'إنهاء' : 'Termination', color: '#c62828' }
    };

    const formatCurrency = (val) => {
        if (!val && val !== 0) return '—';
        return new Intl.NumberFormat(isRTL ? 'ar-SA' : 'en-SA', { style: 'currency', currency: 'SAR', maximumFractionDigits: 0 }).format(val);
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div>
                    <h1 className="workspace-title">
                        <FileText size={24} className="me-2" />
                        {isRTL ? 'تعديلات العقود ومؤشرات الأداء' : 'Contract Amendments & KPIs'}
                    </h1>
                    <p className="workspace-subtitle">
                        {isRTL ? 'تتبع تعديلات العقود ومؤشرات أداء العقد' : 'Track contract amendments and performance indicators'}
                    </p>
                </div>
            </div>

            {/* Contract Selector */}
            <div className="d-flex gap-3 mb-4 align-items-center">
                <label className="form-label mb-0" style={{ whiteSpace: 'nowrap' }}>{isRTL ? 'العقد:' : 'Contract:'}</label>
                <select className="form-input" style={{ maxWidth: 400 }} value={selectedContract}
                    onChange={e => setSelectedContract(e.target.value)}>
                    {contracts.map(c => <option key={c.id} value={c.id}>{c.title || c.contract_number || `#${c.id}`}</option>)}
                </select>
            </div>

            {/* Tabs */}
            <div className="tabs mb-4">
                <button className={`tab ${activeTab === 'amendments' ? 'active' : ''}`} onClick={() => setActiveTab('amendments')}>
                    <FileText size={16} /> <span className="ms-1">{isRTL ? 'التعديلات' : 'Amendments'}</span>
                </button>
                <button className={`tab ${activeTab === 'kpis' ? 'active' : ''}`} onClick={() => setActiveTab('kpis')}>
                    <BarChart3 size={16} /> <span className="ms-1">{isRTL ? 'مؤشرات الأداء' : 'KPIs'}</span>
                </button>
            </div>

            {loading ? (
                <div className="text-center p-5"><div className="spinner-border" /></div>
            ) : activeTab === 'amendments' ? (
                <>
                    <div className="mb-3">
                        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
                            <Plus size={16} className="me-1" /> {isRTL ? 'إضافة تعديل' : 'Add Amendment'}
                        </button>
                    </div>

                    {/* Amendment Form */}
                    {showForm && (
                        <div className="section-card mb-4">
                            <h4 className="mb-3">{isRTL ? 'تعديل جديد' : 'New Amendment'}</h4>
                            <form onSubmit={handleSubmit}>
                                <div className="row g-3">
                                    <div className="col-md-4">
                                        <div className="form-group">
                                            <label className="form-label">{isRTL ? 'نوع التعديل' : 'Type'} *</label>
                                            <select className="form-input" required value={form.amendment_type}
                                                onChange={e => setForm(p => ({ ...p, amendment_type: e.target.value }))}>
                                                {Object.entries(amendmentTypes).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                                            </select>
                                        </div>
                                    </div>
                                    <div className="col-md-4">
                                        <div className="form-group">
                                            <label className="form-label">{isRTL ? 'تاريخ السريان' : 'Effective Date'}</label>
                                            <DateInput className="form-input" value={form.effective_date}
                                                onChange={e => setForm(p => ({ ...p, effective_date: e.target.value }))} />
                                        </div>
                                    </div>
                                    <div className="col-md-4">
                                        <div className="form-group">
                                            <label className="form-label">{isRTL ? 'معتمد من' : 'Approved By'}</label>
                                            <input className="form-input" value={form.approved_by}
                                                onChange={e => setForm(p => ({ ...p, approved_by: e.target.value }))} />
                                        </div>
                                    </div>
                                    <div className="col-md-6">
                                        <div className="form-group">
                                            <label className="form-label">{isRTL ? 'القيمة القديمة' : 'Old Value'}</label>
                                            <input className="form-input" value={form.old_value}
                                                onChange={e => setForm(p => ({ ...p, old_value: e.target.value }))} />
                                        </div>
                                    </div>
                                    <div className="col-md-6">
                                        <div className="form-group">
                                            <label className="form-label">{isRTL ? 'القيمة الجديدة' : 'New Value'}</label>
                                            <input className="form-input" value={form.new_value}
                                                onChange={e => setForm(p => ({ ...p, new_value: e.target.value }))} />
                                        </div>
                                    </div>
                                    <div className="col-md-12">
                                        <div className="form-group">
                                            <label className="form-label">{isRTL ? 'الوصف' : 'Description'} *</label>
                                            <textarea className="form-input" rows={3} required value={form.description}
                                                onChange={e => setForm(p => ({ ...p, description: e.target.value }))} />
                                        </div>
                                    </div>
                                </div>
                                <div className="d-flex gap-2 mt-3">
                                    <button type="submit" className="btn btn-primary"><Save size={16} className="me-1" /> {isRTL ? 'حفظ' : 'Save'}</button>
                                    <button type="button" className="btn btn-outline-secondary" onClick={() => setShowForm(false)}><X size={16} className="me-1" /> {isRTL ? 'إلغاء' : 'Cancel'}</button>
                                </div>
                            </form>
                        </div>
                    )}

                    {/* Amendments list */}
                    <div className="section-card">
                        <div className="data-table-container">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>{isRTL ? 'النوع' : 'Type'}</th>
                                        <th>{isRTL ? 'الوصف' : 'Description'}</th>
                                        <th>{isRTL ? 'القيمة القديمة' : 'Old Value'}</th>
                                        <th>{isRTL ? 'القيمة الجديدة' : 'New Value'}</th>
                                        <th>{isRTL ? 'التاريخ' : 'Effective Date'}</th>
                                        <th>{isRTL ? 'معتمد من' : 'Approved By'}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {amendments.length === 0 ? (
                                        <tr><td colSpan={7} className="text-center p-4">{isRTL ? 'لا توجد تعديلات' : 'No amendments yet'}</td></tr>
                                    ) : amendments.map((a, idx) => (
                                        <tr key={a.id}>
                                            <td>{idx + 1}</td>
                                            <td>
                                                <span className="badge" style={{ background: amendmentTypes[a.amendment_type]?.color || '#6c757d', color: '#fff' }}>
                                                    {amendmentTypes[a.amendment_type]?.label || a.amendment_type}
                                                </span>
                                            </td>
                                            <td>{a.description}</td>
                                            <td>{a.old_value || '—'}</td>
                                            <td>{a.new_value || '—'}</td>
                                            <td>{a.effective_date ? new Date(a.effective_date).toLocaleDateString() : '—'}</td>
                                            <td>{a.approved_by || '—'}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Accounting Note */}
                    <div className="section-card mt-4" style={{ background: '#f0f7ff', border: '1px dashed #90caf9' }}>
                        <h5 style={{ color: '#1565c0' }}>{isRTL ? 'الأثر المحاسبي' : 'Accounting Impact'}</h5>
                        <ul style={{ fontSize: '0.9rem', lineHeight: 1.8 }}>
                            <li><strong>{isRTL ? 'تعديل السعر:' : 'Price Adjustment:'}</strong> {isRTL ? 'يعدّل الإيراد / التكلفة المتبقية بأثر مستقبلي (IAS 8)' : 'Adjusts remaining revenue/cost prospectively (IAS 8)'}</li>
                            <li><strong>{isRTL ? 'تغيير النطاق:' : 'Scope Change:'}</strong> {isRTL ? 'يُعاد حساب نسبة الإنجاز وفق IFRS 15.18' : 'Recalculates % completion per IFRS 15.18'}</li>
                            <li><strong>{isRTL ? 'إنهاء مبكر:' : 'Early Termination:'}</strong> {isRTL ? 'يُثبت مخصص / غرامة — مدين: مصروف غرامات / دائن: مخصصات' : 'Records penalty provision — Dr. Penalty Expense / Cr. Provision for Penalties'}</li>
                        </ul>
                    </div>
                </>
            ) : (
                <>
                    {/* KPIs Dashboard */}
                    {kpis && (
                        <div className="metrics-grid mb-4">
                            <div className="metric-card">
                                <div className="metric-icon" style={{ background: '#e3f2fd' }}><TrendingUp size={22} color="#1565c0" /></div>
                                <div className="metric-info">
                                    <span className="metric-value">{(kpis.utilization_pct || 0).toFixed(1)}%</span>
                                    <span className="metric-label">{isRTL ? 'نسبة الاستخدام' : 'Utilization %'}</span>
                                </div>
                            </div>
                            <div className="metric-card">
                                <div className="metric-icon" style={{ background: '#fff3e0' }}><Calendar size={22} color="#ef6c00" /></div>
                                <div className="metric-info">
                                    <span className="metric-value">{kpis.days_remaining || 0}</span>
                                    <span className="metric-label">{isRTL ? 'أيام متبقية' : 'Days Remaining'}</span>
                                </div>
                            </div>
                            <div className="metric-card">
                                <div className="metric-icon" style={{ background: '#e8f5e9' }}><DollarSign size={22} color="#2e7d32" /></div>
                                <div className="metric-info">
                                    <span className="metric-value">{kpis.invoice_count || 0}</span>
                                    <span className="metric-label">{isRTL ? 'عدد الفواتير' : 'Invoice Count'}</span>
                                </div>
                            </div>
                            <div className="metric-card">
                                <div className="metric-icon" style={{ background: '#fce4ec' }}><DollarSign size={22} color="#c62828" /></div>
                                <div className="metric-info">
                                    <span className="metric-value">{formatCurrency(kpis.outstanding_amount)}</span>
                                    <span className="metric-label">{isRTL ? 'المبالغ المعلقة' : 'Outstanding Amount'}</span>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Contract financial summary */}
                    {kpis && (
                        <div className="section-card">
                            <h4 className="mb-3">{isRTL ? 'ملخص مالي' : 'Financial Summary'}</h4>
                            <div className="row g-3">
                                <div className="col-md-6">
                                    <table className="data-table">
                                        <tbody>
                                            <tr><td><strong>{isRTL ? 'قيمة العقد' : 'Contract Value'}</strong></td><td>{formatCurrency(kpis.contract_value)}</td></tr>
                                            <tr><td><strong>{isRTL ? 'المبلغ المفوتر' : 'Invoiced Amount'}</strong></td><td>{formatCurrency(kpis.invoiced_amount)}</td></tr>
                                            <tr><td><strong>{isRTL ? 'المبلغ المحصل' : 'Collected Amount'}</strong></td><td>{formatCurrency(kpis.collected_amount)}</td></tr>
                                            <tr><td><strong>{isRTL ? 'المتبقي' : 'Outstanding'}</strong></td><td style={{ color: '#c62828' }}>{formatCurrency(kpis.outstanding_amount)}</td></tr>
                                        </tbody>
                                    </table>
                                </div>
                                <div className="col-md-6">
                                    <table className="data-table">
                                        <tbody>
                                            <tr><td><strong>{isRTL ? 'تاريخ البدء' : 'Start Date'}</strong></td><td>{kpis.start_date || '—'}</td></tr>
                                            <tr><td><strong>{isRTL ? 'تاريخ الانتهاء' : 'End Date'}</strong></td><td>{kpis.end_date || '—'}</td></tr>
                                            <tr><td><strong>{isRTL ? 'عدد التعديلات' : 'Amendments'}</strong></td><td>{kpis.amendment_count || 0}</td></tr>
                                            <tr><td><strong>{isRTL ? 'هامش الربح' : 'Profit Margin'}</strong></td><td>{(kpis.profit_margin || 0).toFixed(1)}%</td></tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default ContractAmendments;
