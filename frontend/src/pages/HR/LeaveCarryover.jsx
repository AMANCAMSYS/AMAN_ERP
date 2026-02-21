import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { hrImprovementsAPI } from '../../utils/api';
import { useToast } from '../../context/ToastContext';
import { Calendar, RotateCcw, ArrowRight, Clock } from 'lucide-react';
import '../../components/ModuleStyles.css';

const LeaveCarryover = () => {
    const { t, i18n } = useTranslation();
    const { showToast } = useToast();
    const isRTL = i18n.language === 'ar';
    const [balances, setBalances] = useState([]);
    const [loading, setLoading] = useState(true);
    const [employeeId, setEmployeeId] = useState('');
    const [showCarryover, setShowCarryover] = useState(false);
    const [carryForm, setCarryForm] = useState({ employee_id: '', from_year: new Date().getFullYear() - 1, to_year: new Date().getFullYear(), days: '' });

    const fetchBalance = async (empId) => {
        if (!empId) return;
        try { setLoading(true); const res = await hrImprovementsAPI.getLeaveBalance(empId); setBalances(res.data?.balances || []); }
        catch (err) { showToast(t('hr.error_fetching_balances'), 'error'); } finally { setLoading(false); }
    };

    const handleCarryover = async (e) => {
        e.preventDefault();
        try {
            await hrImprovementsAPI.calculateLeaveCarryover({ employee_id: parseInt(carryForm.employee_id), year: parseInt(carryForm.from_year) });
            showToast(t('hr.leave_carried_success'), 'success');
            setShowCarryover(false); if (employeeId) fetchBalance(employeeId);
        } catch (err) { showToast(err.response?.data?.detail || 'Error', 'error'); }
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className="workspace-title"><span className="p-2 rounded-lg bg-blue-50 text-blue-600"><Calendar size={24} /></span> {t('hr.leave_balance_title')}</h1>
                        <p className="workspace-subtitle">{t('hr.leave_balance_subtitle')}</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => setShowCarryover(true)}><RotateCcw size={18} /> {t('hr.carry_over_btn')}</button>
                </div>
            </div>

            {/* Lookup by employee */}
            <div className="card section-card mb-4">
                <div className="d-flex gap-3 align-items-end">
                    <div className="form-group" style={{ flex: 1 }}>
                        <label className="form-label">{t('hr.leave_employee_id')}</label>
                        <input type="number" className="form-input" placeholder={t('hr.enter_employee_id')} value={employeeId} onChange={e => setEmployeeId(e.target.value)} />
                    </div>
                    <button className="btn btn-primary" onClick={() => fetchBalance(employeeId)} disabled={!employeeId}>{t('hr.view_balances')}</button>
                </div>
            </div>

            {/* Balance Display */}
            {balances.length > 0 && (
                <div className="metrics-grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))' }}>
                    {balances.map((b, i) => (
                        <div key={i} className="card section-card text-center p-4">
                            <div className="text-sm text-muted mb-2">{b.leave_type === 'annual' ? t('hr.annual_leave') : b.leave_type}</div>
                            <div className="text-3xl font-bold text-primary mb-2">{b.remaining_days ?? 0}</div>
                            <div className="text-xs text-muted">{t('hr.days_remaining')}</div>
                            {b.entitled_days > 0 && <div className="text-xs mt-2">{t('hr.of_total_days', { total: b.entitled_days })}</div>}
                            {b.carried_days > 0 && <div className="text-xs text-blue-600 mt-1"><RotateCcw size={12} style={{ display: 'inline' }} /> {t('hr.carried_over', { count: b.carried_days })}</div>}
                        </div>
                    ))}
                </div>
            )}

            {!loading && balances.length === 0 && employeeId && (
                <div className="card section-card text-center p-6 text-muted">{t('hr.no_leave_balances')}</div>
            )}

            {/* Carryover Modal */}
            {showCarryover && (
                <div className="modal-overlay" onClick={() => setShowCarryover(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 420 }}>
                        <h3 className="modal-title"><RotateCcw size={20} /> {t('hr.carry_over_btn')}</h3>
                        <form onSubmit={handleCarryover} className="space-y-4">
                            <div className="form-group"><label className="form-label">{t('hr.leave_employee_id')}</label>
                                <input type="number" className="form-input" required value={carryForm.employee_id} onChange={e => setCarryForm({ ...carryForm, employee_id: e.target.value })} /></div>
                            <div className="grid grid-cols-2 gap-3">
                                <div className="form-group"><label className="form-label">{t('hr.from_year')}</label>
                                    <input type="number" className="form-input" required value={carryForm.from_year} onChange={e => setCarryForm({ ...carryForm, from_year: e.target.value })} /></div>
                                <div className="form-group"><label className="form-label">{t('hr.to_year')}</label>
                                    <input type="number" className="form-input" required value={carryForm.to_year} onChange={e => setCarryForm({ ...carryForm, to_year: e.target.value })} /></div>
                            </div>
                            <div className="form-group"><label className="form-label">{t('hr.days_to_carry')}</label>
                                <input type="number" className="form-input" required min="1" value={carryForm.days} onChange={e => setCarryForm({ ...carryForm, days: e.target.value })} /></div>
                            <div className="d-flex gap-3 pt-3"><button type="submit" className="btn btn-primary flex-1">{t('hr.carry_over_submit')}</button>
                                <button type="button" className="btn btn-secondary" onClick={() => setShowCarryover(false)}>{t('hr.cancel')}</button></div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default LeaveCarryover;
