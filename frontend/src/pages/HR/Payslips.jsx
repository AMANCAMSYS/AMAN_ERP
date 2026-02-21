import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { hrImprovementsAPI } from '../../utils/api';
import { useToast } from '../../context/ToastContext';
import { getCurrency } from '../../utils/auth';
import { formatNumber } from '../../utils/format';
import { FileText, Calculator, Download, Eye, RefreshCw } from 'lucide-react';
import '../../components/ModuleStyles.css';

const Payslips = () => {
    const { t, i18n } = useTranslation();
    const { showToast } = useToast();
    const currency = getCurrency();
    const isRTL = i18n.language === 'ar';
    const [payslips, setPayslips] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showGenerate, setShowGenerate] = useState(false);
    const [genForm, setGenForm] = useState({ employee_id: '', month: new Date().getMonth() + 1, year: new Date().getFullYear() });

    useEffect(() => { fetchPayslips(); }, []);

    const fetchPayslips = async () => {
        try { setLoading(true); const res = await hrImprovementsAPI.listPayslips(); setPayslips(res.data || []); }
        catch (err) { console.error(err); } finally { setLoading(false); }
    };

    const handleGenerate = async (e) => {
        e.preventDefault();
        try {
            await hrImprovementsAPI.generatePayslip({ employee_id: parseInt(genForm.employee_id), month: parseInt(genForm.month), year: parseInt(genForm.year) });
            showToast(t('hr.payslip_generated'), 'success');
            setShowGenerate(false); fetchPayslips();
        } catch (err) { showToast(err.response?.data?.detail || t('common.error'), 'error'); }
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className="workspace-title"><span className="p-2 rounded-lg bg-emerald-50 text-emerald-600"><FileText size={24} /></span> {t('hr.payslips_title')}</h1>
                        <p className="workspace-subtitle">{t('hr.payslips_subtitle')}</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => setShowGenerate(true)}><Calculator size={18} /> {t('hr.generate_payslip')}</button>
                </div>
            </div>

            <div className="card section-card">
                {loading ? <div className="text-center p-4">...</div> : (
                    <div className="data-table-container">
                        <table className="data-table">
                            <thead><tr>
                                <th>{t('hr.col_employee')}</th>
                                <th>{t('hr.col_month')}</th>
                                <th>{t('hr.col_basic_salary')}</th>
                                <th>{t('hr.col_allowances')}</th>
                                <th>{t('hr.col_deductions')}</th>
                                <th>{t('hr.col_net_pay')}</th>
                                <th>{t('hr.col_status')}</th>
                            </tr></thead>
                            <tbody>
                                {payslips.map(p => (
                                    <tr key={p.id}>
                                        <td className="font-medium">{p.employee_name || `#${p.employee_id}`}</td>
                                        <td>{p.month}/{p.year}</td>
                                        <td>{formatNumber(p.basic_salary)} {currency}</td>
                                        <td className="text-success">+{formatNumber(p.total_allowances || 0)} {currency}</td>
                                        <td className="text-danger">-{formatNumber(p.total_deductions || 0)} {currency}</td>
                                        <td className="font-bold">{formatNumber(p.net_pay)} {currency}</td>
                                        <td><span className={`badge ${p.status === 'paid' ? 'bg-green-100 text-green-700' : p.status === 'approved' ? 'bg-blue-100 text-blue-700' : 'bg-yellow-100 text-yellow-700'}`}>{p.status === 'paid' ? (t('hr.payslip_status_paid')) : p.status === 'approved' ? (t('hr.payslip_status_approved')) : (t('hr.payslip_status_draft'))}</span></td>
                                    </tr>
                                ))}
                                {payslips.length === 0 && <tr><td colSpan="7" className="text-center text-muted p-4">{t('hr.no_payslips')}</td></tr>}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {showGenerate && (
                <div className="modal-overlay" onClick={() => setShowGenerate(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 420 }}>
                        <h3 className="modal-title">{t('hr.generate_modal_title')}</h3>
                        <form onSubmit={handleGenerate} className="space-y-4">
                            <div className="form-group"><label className="form-label">{t('hr.employee_id')}</label>
                                <input type="number" className="form-input" required value={genForm.employee_id} onChange={e => setGenForm({ ...genForm, employee_id: e.target.value })} /></div>
                            <div className="grid grid-cols-2 gap-3">
                                <div className="form-group"><label className="form-label">{t('hr.col_month')}</label>
                                    <select className="form-input" value={genForm.month} onChange={e => setGenForm({ ...genForm, month: e.target.value })}>
                                        {[...Array(12)].map((_, i) => <option key={i + 1} value={i + 1}>{i + 1}</option>)}
                                    </select></div>
                                <div className="form-group"><label className="form-label">{t('hr.year')}</label>
                                    <input type="number" className="form-input" value={genForm.year} onChange={e => setGenForm({ ...genForm, year: e.target.value })} /></div>
                            </div>
                            <div className="d-flex gap-3 pt-3"><button type="submit" className="btn btn-primary flex-1"><Calculator size={16} /> {t('hr.generate_btn')}</button>
                                <button type="button" className="btn btn-secondary" onClick={() => setShowGenerate(false)}>{t('hr.cancel')}</button></div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Payslips;
