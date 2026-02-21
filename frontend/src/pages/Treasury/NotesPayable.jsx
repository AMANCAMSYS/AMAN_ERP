import { useState, useEffect } from 'react';
import { getCurrency } from '../../utils/auth';
import { useTranslation } from 'react-i18next';
import { notesAPI, treasuryAPI, inventoryAPI } from '../../utils/api';
import { FileText, Plus, Eye, CheckCircle, XCircle, AlertTriangle, Clock } from 'lucide-react';
import { toastEmitter } from '../../utils/toastEmitter';
import { useBranch } from '../../context/BranchContext';

import DateInput from '../../components/common/DateInput';
import { formatDate, formatDateTime } from '../../utils/dateUtils';
const NotesPayable = () => {
    const { t } = useTranslation();
    const { currentBranch } = useBranch();
    const [notes, setNotes] = useState([]);
    const currency = getCurrency() || '';
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState('');
    const [showCreate, setShowCreate] = useState(false);
    const [showDetail, setShowDetail] = useState(null);
    const [showPay, setShowPay] = useState(null);
    const [showProtest, setShowProtest] = useState(null);
    const [suppliers, setSuppliers] = useState([]);
    const [treasuryAccounts, setTreasuryAccounts] = useState([]);
    const [form, setForm] = useState({
        note_number: '', beneficiary_name: '', bank_name: '', amount: '',
        currency: getCurrency(), issue_date: new Date().toISOString().split('T')[0],
        due_date: '', maturity_date: '', party_id: '', treasury_account_id: '', notes: ''
    });
    const [payForm, setPayForm] = useState({ payment_date: new Date().toISOString().split('T')[0], treasury_account_id: '' });
    const [protestForm, setProtestForm] = useState({ protest_date: new Date().toISOString().split('T')[0], reason: '' });

    useEffect(() => { loadData(); }, [currentBranch, statusFilter]);

    const loadData = async () => {
        try {
            setLoading(true);
            const params = { branch_id: currentBranch?.id };
            if (statusFilter) params.status_filter = statusFilter;
            const [notesRes, statsRes] = await Promise.all([
                notesAPI.listPayable(params),
                notesAPI.payableStats({ branch_id: currentBranch?.id })
            ]);
            setNotes(notesRes.data);
            setStats(statsRes.data);
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    const loadCreateData = async () => {
        try {
            const [suppRes, treasRes] = await Promise.all([
                inventoryAPI.listSuppliers({ limit: 500 }),
                treasuryAPI.listAccounts(currentBranch?.id)
            ]);
            setSuppliers(suppRes.data || []);
            setTreasuryAccounts((treasRes.data || []).filter(a => a.account_type === 'bank'));
        } catch (e) { console.error(e); }
    };

    const handleCreate = async () => {
        if (!form.note_number || !form.amount || !form.due_date) {
            toastEmitter.emit('يرجى ملء الحقول المطلوبة', 'error'); return;
        }
        try {
            await notesAPI.createPayable({ ...form, amount: parseFloat(form.amount), branch_id: currentBranch?.id });
            toastEmitter.emit('تم إنشاء ورقة الدفع بنجاح', 'success');
            setShowCreate(false);
            setForm({ note_number: '', beneficiary_name: '', bank_name: '', amount: '', currency: getCurrency(),
                issue_date: new Date().toISOString().split('T')[0], due_date: '', maturity_date: '',
                party_id: '', treasury_account_id: '', notes: '' });
            loadData();
        } catch (e) { toastEmitter.emit(e.response?.data?.detail || 'خطأ', 'error'); }
    };

    const handlePay = async () => {
        try {
            await notesAPI.payPayable(showPay.id, payForm);
            toastEmitter.emit('تم سداد ورقة الدفع', 'success');
            setShowPay(null);
            loadData();
        } catch (e) { toastEmitter.emit(e.response?.data?.detail || 'خطأ', 'error'); }
    };

    const handleProtest = async () => {
        try {
            await notesAPI.protestPayable(showProtest.id, protestForm);
            toastEmitter.emit('تم رفض ورقة الدفع', 'success');
            setShowProtest(null);
            loadData();
        } catch (e) { toastEmitter.emit(e.response?.data?.detail || 'خطأ', 'error'); }
    };

    const fmt = (n) => Number(n || 0).toLocaleString('en', { minimumFractionDigits: 2 });
    const isOverdue = (note) => note.status === 'issued' && new Date(note.due_date) < new Date();
    const statusBadge = (s) => {
        const map = { issued: 'badge-warning', paid: 'badge-success', protested: 'badge-danger' };
        const labels = { issued: 'صادرة', paid: 'مسددة', protested: 'مرفوضة' };
        return <span className={`badge ${map[s] || 'badge-secondary'}`}>{labels[s] || s}</span>;
    };

    if (loading) return <div className="page-center"><span className="loading"></span></div>;

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div>
                    <h1 className="workspace-title">📜 أوراق الدفع</h1>
                    <p className="workspace-subtitle">إدارة وتتبع أوراق الدفع (الكمبيالات / السندات لأمر)</p>
                </div>
                <button className="btn btn-primary" onClick={() => { setShowCreate(true); loadCreateData(); }}>
                    <Plus size={16} /> إنشاء ورقة دفع
                </button>
            </div>

            {/* Stats */}
            {stats && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                    <div className="card p-3 text-center">
                        <Clock size={24} className="text-warning mb-2" />
                        <div className="small text-muted">صادرة</div>
                        <div className="fw-bold fs-4">{stats.issued.count}</div>
                        <div className="small text-muted">{fmt(stats.issued.total)} {currency}</div>
                    </div>
                    <div className="card p-3 text-center">
                        <CheckCircle size={24} className="text-success mb-2" />
                        <div className="small text-muted">مسددة</div>
                        <div className="fw-bold fs-4 text-success">{stats.paid.count}</div>
                        <div className="small text-muted">{fmt(stats.paid.total)} {currency}</div>
                    </div>
                    <div className="card p-3 text-center">
                        <XCircle size={24} className="text-danger mb-2" />
                        <div className="small text-muted">مرفوضة</div>
                        <div className="fw-bold fs-4 text-danger">{stats.protested.count}</div>
                        <div className="small text-muted">{fmt(stats.protested.total)} {currency}</div>
                    </div>
                    <div className="card p-3 text-center">
                        <AlertTriangle size={24} className="text-danger mb-2" />
                        <div className="small text-muted">متأخرة</div>
                        <div className="fw-bold fs-4 text-danger">{stats.overdue.count}</div>
                        <div className="small text-muted">{fmt(stats.overdue.total)} {currency}</div>
                    </div>
                </div>
            )}

            {/* Filters */}
            <div className="card p-3 mb-3">
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                    <select className="form-input" style={{ maxWidth: '200px' }} value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
                        <option value="">جميع الحالات</option>
                        <option value="issued">صادرة</option>
                        <option value="paid">مسددة</option>
                        <option value="protested">مرفوضة</option>
                    </select>
                    <span className="text-muted small">{notes.length} ورقة</span>
                </div>
            </div>

            {/* Table */}
            <div className="card">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>رقم الورقة</th>
                            <th>المستفيد</th>
                            <th>المورد</th>
                            <th>البنك</th>
                            <th className="text-end">المبلغ</th>
                            <th>تاريخ الاستحقاق</th>
                            <th>الحالة</th>
                            <th>إجراءات</th>
                        </tr>
                    </thead>
                    <tbody>
                        {notes.length === 0 ? (
                            <tr><td colSpan="8" className="text-center py-4 text-muted">لا توجد أوراق دفع</td></tr>
                        ) : notes.map(note => (
                            <tr key={note.id} style={isOverdue(note) ? { backgroundColor: 'rgba(255,0,0,0.05)' } : {}}>
                                <td className="fw-bold">{note.note_number}</td>
                                <td>{note.beneficiary_name || '-'}</td>
                                <td>{note.party_name || '-'}</td>
                                <td>{note.bank_name || '-'}</td>
                                <td className="text-end font-monospace fw-bold">{fmt(note.amount)}</td>
                                <td>
                                    {formatDate(note.due_date)}
                                    {isOverdue(note) && <span className="badge badge-danger ms-1" style={{ fontSize: '10px' }}>متأخر</span>}
                                </td>
                                <td>{statusBadge(note.status)}</td>
                                <td>
                                    <div style={{ display: 'flex', gap: '4px' }}>
                                        <button className="btn btn-sm btn-light" onClick={() => setShowDetail(note)} title="عرض">
                                            <Eye size={14} />
                                        </button>
                                        {note.status === 'issued' && (
                                            <>
                                                <button className="btn btn-sm btn-success" onClick={() => { setShowPay(note); loadCreateData(); }} title="سداد">
                                                    <CheckCircle size={14} />
                                                </button>
                                                <button className="btn btn-sm btn-danger" onClick={() => setShowProtest(note)} title="رفض">
                                                    <XCircle size={14} />
                                                </button>
                                            </>
                                        )}
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Create Modal */}
            {showCreate && (
                <div className="modal-overlay" onClick={() => setShowCreate(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '600px' }}>
                        <div className="modal-header">
                            <h3>إنشاء ورقة دفع</h3>
                            <button className="btn-icon" onClick={() => setShowCreate(false)}>&times;</button>
                        </div>
                        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                                <div className="form-group">
                                    <label className="form-label">رقم الورقة *</label>
                                    <input className="form-input" value={form.note_number} onChange={e => setForm({ ...form, note_number: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">المبلغ *</label>
                                    <input type="number" step="0.01" className="form-input" value={form.amount} onChange={e => setForm({ ...form, amount: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">اسم المستفيد</label>
                                    <input className="form-input" value={form.beneficiary_name} onChange={e => setForm({ ...form, beneficiary_name: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">البنك</label>
                                    <input className="form-input" value={form.bank_name} onChange={e => setForm({ ...form, bank_name: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">تاريخ الإصدار</label>
                                    <DateInput className="form-input" value={formatDate(form.issue_date)} onChange={e => setForm({ ...form, issue_date: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">تاريخ الاستحقاق *</label>
                                    <DateInput className="form-input" value={formatDate(form.due_date)} onChange={e => setForm({ ...form, due_date: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">المورد</label>
                                    <select className="form-input" value={form.party_id} onChange={e => setForm({ ...form, party_id: e.target.value })}>
                                        <option value="">-- اختر --</option>
                                        {suppliers.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">حساب الخزينة</label>
                                    <select className="form-input" value={form.treasury_account_id} onChange={e => setForm({ ...form, treasury_account_id: e.target.value })}>
                                        <option value="">-- اختر --</option>
                                        {treasuryAccounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                                    </select>
                                </div>
                            </div>
                            <div className="form-group">
                                <label className="form-label">ملاحظات</label>
                                <textarea className="form-input" rows="2" value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} />
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-light" onClick={() => setShowCreate(false)}>إلغاء</button>
                            <button className="btn btn-primary" onClick={handleCreate}>إنشاء</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Detail Modal */}
            {showDetail && (
                <div className="modal-overlay" onClick={() => setShowDetail(null)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '500px' }}>
                        <div className="modal-header">
                            <h3>تفاصيل ورقة الدفع</h3>
                            <button className="btn-icon" onClick={() => setShowDetail(null)}>&times;</button>
                        </div>
                        <div className="modal-body">
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                                {[
                                    ['رقم الورقة', showDetail.note_number],
                                    ['المبلغ', fmt(showDetail.amount) + ' ' + (showDetail.currency || '')],
                                    ['المستفيد', showDetail.beneficiary_name],
                                    ['البنك', showDetail.bank_name],
                                    ['المورد', showDetail.party_name],
                                    ['تاريخ الإصدار', showDetail.issue_date],
                                    ['تاريخ الاستحقاق', showDetail.due_date],
                                    ['الحالة', showDetail.status],
                                    ['تاريخ السداد', showDetail.payment_date],
                                    ['تاريخ الرفض', showDetail.protest_date],
                                    ['سبب الرفض', showDetail.protest_reason],
                                ].map(([label, val], i) => val ? (
                                    <div key={i}><span className="small text-muted">{label}</span><div className="fw-bold">{val}</div></div>
                                ) : null)}
                            </div>
                            {showDetail.notes && <div className="mt-3"><span className="small text-muted">ملاحظات</span><div>{showDetail.notes}</div></div>}
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-light" onClick={() => setShowDetail(null)}>إغلاق</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Pay Modal */}
            {showPay && (
                <div className="modal-overlay" onClick={() => setShowPay(null)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '400px' }}>
                        <div className="modal-header">
                            <h3>سداد ورقة الدفع</h3>
                            <button className="btn-icon" onClick={() => setShowPay(null)}>&times;</button>
                        </div>
                        <div className="modal-body">
                            <p>ورقة رقم <strong>{showPay.note_number}</strong> بمبلغ <strong>{fmt(showPay.amount)}</strong></p>
                            <div className="form-group mb-3">
                                <label className="form-label">تاريخ السداد</label>
                                <DateInput className="form-input" value={formatDate(payForm.payment_date)}
                                    onChange={e => setPayForm({ ...payForm, payment_date: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">حساب البنك</label>
                                <select className="form-input" value={payForm.treasury_account_id}
                                    onChange={e => setPayForm({ ...payForm, treasury_account_id: e.target.value })}>
                                    <option value="">-- اختر --</option>
                                    {treasuryAccounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                                </select>
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-light" onClick={() => setShowPay(null)}>إلغاء</button>
                            <button className="btn btn-success" onClick={handlePay}>تأكيد السداد</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Protest Modal */}
            {showProtest && (
                <div className="modal-overlay" onClick={() => setShowProtest(null)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '400px' }}>
                        <div className="modal-header">
                            <h3>رفض ورقة الدفع</h3>
                            <button className="btn-icon" onClick={() => setShowProtest(null)}>&times;</button>
                        </div>
                        <div className="modal-body">
                            <p>ورقة رقم <strong>{showProtest.note_number}</strong> بمبلغ <strong>{fmt(showProtest.amount)}</strong></p>
                            <div className="form-group mb-3">
                                <label className="form-label">تاريخ الرفض</label>
                                <DateInput className="form-input" value={protestForm.protest_date}
                                    onChange={e => setProtestForm({ ...protestForm, protest_date: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">سبب الرفض</label>
                                <textarea className="form-input" rows="2" value={protestForm.reason}
                                    onChange={e => setProtestForm({ ...protestForm, reason: e.target.value })} />
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-light" onClick={() => setShowProtest(null)}>إلغاء</button>
                            <button className="btn btn-danger" onClick={handleProtest}>تأكيد الرفض</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default NotesPayable;
