import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { expensesAPI } from '../../utils/api';
import { useToast } from '../../context/ToastContext';
import { getCurrency } from '../../utils/auth';
import { formatNumber } from '../../utils/format';
import { FileText, Plus, Trash2, Edit3, CheckCircle, AlertTriangle, Save, X } from 'lucide-react';
import BackButton from '../../components/common/BackButton';
import '../../components/ModuleStyles.css';

const ExpensePolicies = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const { showToast } = useToast();
    const currency = getCurrency();
    const [policies, setPolicies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [editingId, setEditingId] = useState(null);
    const [form, setForm] = useState({
        name: '', expense_type: '', department_id: null,
        daily_limit: '', monthly_limit: '', annual_limit: '',
        requires_receipt: true, requires_approval: true,
        auto_approve_below: '', is_active: true
    });

    useEffect(() => { fetchPolicies(); }, []);

    const fetchPolicies = async () => {
        try {
            setLoading(true);
            const res = await expensesAPI.listPolicies();
            setPolicies(res.data || []);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editingId) {
                await expensesAPI.updatePolicy(editingId, form);
                showToast(isRTL ? 'تم تحديث السياسة' : 'Policy updated', 'success');
            } else {
                await expensesAPI.createPolicy(form);
                showToast(isRTL ? 'تم إنشاء السياسة' : 'Policy created', 'success');
            }
            resetForm();
            fetchPolicies();
        } catch (err) {
            showToast(err.response?.data?.detail || 'Error', 'error');
        }
    };

    const handleEdit = (p) => {
        setEditingId(p.id);
        setForm({
            name: p.name, expense_type: p.expense_type || '',
            department_id: p.department_id, daily_limit: p.daily_limit || '',
            monthly_limit: p.monthly_limit || '', annual_limit: p.annual_limit || '',
            requires_receipt: p.requires_receipt, requires_approval: p.requires_approval,
            auto_approve_below: p.auto_approve_below || '', is_active: p.is_active
        });
        setShowForm(true);
    };

    const handleDelete = async (id) => {
        if (!confirm(isRTL ? 'هل أنت متأكد من حذف هذه السياسة؟' : 'Delete this policy?')) return;
        try {
            await expensesAPI.deletePolicy(id);
            showToast(isRTL ? 'تم حذف السياسة' : 'Policy deleted', 'success');
            fetchPolicies();
        } catch (err) {
            showToast(err.response?.data?.detail || 'Error', 'error');
        }
    };

    const resetForm = () => {
        setShowForm(false);
        setEditingId(null);
        setForm({ name: '', expense_type: '', department_id: null, daily_limit: '', monthly_limit: '', annual_limit: '', requires_receipt: true, requires_approval: true, auto_approve_below: '', is_active: true });
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="d-flex align-items-center justify-content-between w-100">
                    <div>
                        <h1 className="workspace-title">
                            <FileText size={24} className="me-2" />
                            {isRTL ? 'سياسات المصروفات' : 'Expense Policies'}
                        </h1>
                        <p className="workspace-subtitle">
                            {isRTL ? 'إدارة حدود الصرف والموافقات التلقائية حسب الفئة والقسم' : 'Manage spending limits and auto-approval rules by category and department'}
                        </p>
                    </div>
                    <button className="btn btn-primary" onClick={() => { resetForm(); setShowForm(true); }}>
                        <Plus size={16} className="me-1" /> {isRTL ? 'سياسة جديدة' : 'New Policy'}
                    </button>
                </div>
            </div>

            {/* Metrics */}
            <div className="metrics-grid mb-4">
                <div className="metric-card">
                    <div className="metric-icon" style={{ background: '#e8f5e9' }}><CheckCircle size={22} color="#2e7d32" /></div>
                    <div className="metric-info">
                        <span className="metric-value">{policies.filter(p => p.is_active).length}</span>
                        <span className="metric-label">{isRTL ? 'سياسات نشطة' : 'Active Policies'}</span>
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-icon" style={{ background: '#fff3e0' }}><AlertTriangle size={22} color="#ef6c00" /></div>
                    <div className="metric-info">
                        <span className="metric-value">{policies.filter(p => p.requires_approval).length}</span>
                        <span className="metric-label">{isRTL ? 'تتطلب موافقة' : 'Require Approval'}</span>
                    </div>
                </div>
            </div>

            {/* Form Modal */}
            {showForm && (
                <div className="section-card mb-4">
                    <h3 className="mb-3">{editingId ? (isRTL ? 'تعديل السياسة' : 'Edit Policy') : (isRTL ? 'سياسة جديدة' : 'New Policy')}</h3>
                    <form onSubmit={handleSubmit}>
                        <div className="row g-3">
                            <div className="col-md-4">
                                <div className="form-group">
                                    <label className="form-label">{isRTL ? 'اسم السياسة' : 'Policy Name'} *</label>
                                    <input className="form-input" required value={form.name}
                                        onChange={e => setForm(p => ({ ...p, name: e.target.value }))} />
                                </div>
                            </div>
                            <div className="col-md-4">
                                <div className="form-group">
                                    <label className="form-label">{isRTL ? 'نوع المصروف' : 'Expense Type'}</label>
                                    <select className="form-input" value={form.expense_type}
                                        onChange={e => setForm(p => ({ ...p, expense_type: e.target.value }))}>
                                        <option value="">{isRTL ? 'الكل' : 'All'}</option>
                                        <option value="travel">{isRTL ? 'سفر' : 'Travel'}</option>
                                        <option value="meals">{isRTL ? 'وجبات' : 'Meals'}</option>
                                        <option value="supplies">{isRTL ? 'مستلزمات' : 'Supplies'}</option>
                                        <option value="transportation">{isRTL ? 'نقل' : 'Transportation'}</option>
                                        <option value="entertainment">{isRTL ? 'ترفيه' : 'Entertainment'}</option>
                                        <option value="other">{isRTL ? 'أخرى' : 'Other'}</option>
                                    </select>
                                </div>
                            </div>
                            <div className="col-md-4">
                                <div className="form-group">
                                    <label className="form-label">{isRTL ? 'الحد اليومي' : 'Daily Limit'} ({currency})</label>
                                    <input className="form-input" type="number" step="0.01" value={form.daily_limit}
                                        onChange={e => setForm(p => ({ ...p, daily_limit: e.target.value }))} />
                                </div>
                            </div>
                            <div className="col-md-4">
                                <div className="form-group">
                                    <label className="form-label">{isRTL ? 'الحد الشهري' : 'Monthly Limit'} ({currency})</label>
                                    <input className="form-input" type="number" step="0.01" value={form.monthly_limit}
                                        onChange={e => setForm(p => ({ ...p, monthly_limit: e.target.value }))} />
                                </div>
                            </div>
                            <div className="col-md-4">
                                <div className="form-group">
                                    <label className="form-label">{isRTL ? 'الحد السنوي' : 'Annual Limit'} ({currency})</label>
                                    <input className="form-input" type="number" step="0.01" value={form.annual_limit}
                                        onChange={e => setForm(p => ({ ...p, annual_limit: e.target.value }))} />
                                </div>
                            </div>
                            <div className="col-md-4">
                                <div className="form-group">
                                    <label className="form-label">{isRTL ? 'موافقة تلقائية أقل من' : 'Auto-approve below'} ({currency})</label>
                                    <input className="form-input" type="number" step="0.01" value={form.auto_approve_below}
                                        onChange={e => setForm(p => ({ ...p, auto_approve_below: e.target.value }))} />
                                </div>
                            </div>
                            <div className="col-md-4 d-flex align-items-end gap-3">
                                <label className="d-flex align-items-center gap-2">
                                    <input type="checkbox" checked={form.requires_receipt}
                                        onChange={e => setForm(p => ({ ...p, requires_receipt: e.target.checked }))} />
                                    {isRTL ? 'يتطلب إيصال' : 'Requires Receipt'}
                                </label>
                                <label className="d-flex align-items-center gap-2">
                                    <input type="checkbox" checked={form.requires_approval}
                                        onChange={e => setForm(p => ({ ...p, requires_approval: e.target.checked }))} />
                                    {isRTL ? 'يتطلب موافقة' : 'Requires Approval'}
                                </label>
                            </div>
                        </div>
                        <div className="d-flex gap-2 mt-3">
                            <button type="submit" className="btn btn-primary"><Save size={16} className="me-1" /> {isRTL ? 'حفظ' : 'Save'}</button>
                            <button type="button" className="btn btn-outline-secondary" onClick={resetForm}><X size={16} className="me-1" /> {isRTL ? 'إلغاء' : 'Cancel'}</button>
                        </div>
                    </form>
                </div>
            )}

            {/* Policies Table */}
            <div className="section-card">
                {loading ? (
                    <div className="text-center p-5"><div className="spinner-border" /></div>
                ) : (
                    <div className="data-table-container">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>{isRTL ? 'السياسة' : 'Policy'}</th>
                                    <th>{isRTL ? 'نوع المصروف' : 'Type'}</th>
                                    <th>{isRTL ? 'الحد اليومي' : 'Daily'}</th>
                                    <th>{isRTL ? 'الحد الشهري' : 'Monthly'}</th>
                                    <th>{isRTL ? 'الحد السنوي' : 'Annual'}</th>
                                    <th>{isRTL ? 'موافقة تلقائية' : 'Auto-Approve'}</th>
                                    <th>{isRTL ? 'الحالة' : 'Status'}</th>
                                    <th>{isRTL ? 'إجراءات' : 'Actions'}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {policies.length === 0 ? (
                                    <tr><td colSpan={8} className="text-center p-4">{isRTL ? 'لا توجد سياسات' : 'No policies defined'}</td></tr>
                                ) : policies.map(p => (
                                    <tr key={p.id}>
                                        <td><strong>{p.name}</strong></td>
                                        <td>{p.expense_type || (isRTL ? 'الكل' : 'All')}</td>
                                        <td>{p.daily_limit ? `${formatNumber(p.daily_limit)} ${currency}` : '—'}</td>
                                        <td>{p.monthly_limit ? `${formatNumber(p.monthly_limit)} ${currency}` : '—'}</td>
                                        <td>{p.annual_limit ? `${formatNumber(p.annual_limit)} ${currency}` : '—'}</td>
                                        <td>{p.auto_approve_below ? `< ${formatNumber(p.auto_approve_below)} ${currency}` : '—'}</td>
                                        <td>
                                            <span className={`badge ${p.is_active ? 'bg-success' : 'bg-secondary'}`}>
                                                {p.is_active ? (isRTL ? 'نشط' : 'Active') : (isRTL ? 'معطل' : 'Inactive')}
                                            </span>
                                        </td>
                                        <td>
                                            <div className="d-flex gap-1">
                                                <button className="btn btn-sm btn-outline-primary" onClick={() => handleEdit(p)}>
                                                    <Edit3 size={14} />
                                                </button>
                                                <button className="btn btn-sm btn-outline-danger" onClick={() => handleDelete(p.id)}>
                                                    <Trash2 size={14} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ExpensePolicies;
