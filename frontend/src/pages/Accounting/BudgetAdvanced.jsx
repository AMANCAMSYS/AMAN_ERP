import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { budgetImprovementsAPI } from '../../utils/api';
import { useToast } from '../../context/ToastContext';
import { getCurrency } from '../../utils/auth';
import { formatNumber } from '../../utils/format';
import { TrendingUp, BarChart3, Plus, GitCompareArrows } from 'lucide-react';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';

const BudgetAdvanced = () => {
    const { t, i18n } = useTranslation();
    const { showToast } = useToast();
    const currency = getCurrency();
    const isRTL = i18n.language === 'ar';
    const [activeTab, setActiveTab] = useState('costcenter');
    const [ccBudgets, setCcBudgets] = useState([]);
    const [multiYear, setMultiYear] = useState([]);
    const [comparison, setComparison] = useState(null);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [ccForm, setCcForm] = useState({ cost_center_id: '', budget_id: '', amount: '' });
    const [myForm, setMyForm] = useState({ name: '', start_year: new Date().getFullYear(), end_year: new Date().getFullYear() + 2, annual_amount: '' });
    const [compForm, setCompForm] = useState({ budget_id_1: '', budget_id_2: '' });

    useEffect(() => { fetchData(); }, [activeTab]);

    const fetchData = async () => {
        try {
            setLoading(true);
            if (activeTab === 'costcenter') { const res = await budgetImprovementsAPI.listCostCenterBudgets(); setCcBudgets(res.data || []); }
            else if (activeTab === 'multiyear') { const res = await budgetImprovementsAPI.listMultiYearBudgets(); setMultiYear(res.data || []); }
        } catch (err) { console.error(err); } finally { setLoading(false); }
    };

    const handleCreateCC = async (e) => {
        e.preventDefault();
        try {
            await budgetImprovementsAPI.createCostCenterBudget({ cost_center_id: parseInt(ccForm.cost_center_id), budget_id: parseInt(ccForm.budget_id), amount: parseFloat(ccForm.amount) });
            showToast(t('budget.cc_budget_created'), 'success');
            setShowModal(false); fetchData();
        } catch (err) { showToast(err.response?.data?.detail || t('common.error'), 'error'); }
    };

    const handleCreateMY = async (e) => {
        e.preventDefault();
        try {
            await budgetImprovementsAPI.createMultiYearBudget({ name: myForm.name, start_year: parseInt(myForm.start_year), end_year: parseInt(myForm.end_year), annual_amount: parseFloat(myForm.annual_amount) });
            showToast(t('budget.multi_year_created'), 'success');
            setShowModal(false); fetchData();
        } catch (err) { showToast(err.response?.data?.detail || t('common.error'), 'error'); }
    };

    const handleCompare = async () => {
        if (!compForm.budget_id_1 || !compForm.budget_id_2) return;
        try {
            const res = await budgetImprovementsAPI.compareBudgets(compForm.budget_id_1, compForm.budget_id_2);
            setComparison(res.data);
        } catch (err) { showToast(t('errors.comparison_failed'), 'error'); }
    };

    const tabs = [
        { key: 'costcenter', label: t('budget.tab_cost_centers'), icon: BarChart3 },
        { key: 'multiyear', label: t('budget.tab_multi_year'), icon: TrendingUp },
        { key: 'comparison', label: t('budget.tab_comparison'), icon: GitCompareArrows },
    ];

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className="workspace-title"><span className="p-2 rounded-lg bg-amber-50 text-amber-600"><BarChart3 size={24} /></span> {t('budget.advanced_title')}</h1>
                        <p className="workspace-subtitle">{t('budget.advanced_subtitle')}</p>
                    </div>
                    {activeTab !== 'comparison' && <button className="btn btn-primary" onClick={() => setShowModal(true)}><Plus size={18} /> {t('budget.new')}</button>}
                </div>
            </div>

            <div className="d-flex gap-2 mb-4">
                {tabs.map(tab => { const Icon = tab.icon; return <button key={tab.key} onClick={() => setActiveTab(tab.key)} className={`btn ${activeTab === tab.key ? 'btn-primary' : 'btn-secondary'}`}><Icon size={16} /> {tab.label}</button>; })}
            </div>

            <div className="card section-card">
                {loading && activeTab !== 'comparison' ? <div className="text-center p-4">...</div> : activeTab === 'costcenter' ? (
                    <div className="data-table-container">
                        <table className="data-table">
                            <thead><tr>
                                <th>{t('budget.col_cost_center')}</th>
                                <th>{t('budget.col_budget')}</th>
                                <th>{t('budget.col_allocated')}</th>
                                <th>{t('budget.col_spent')}</th>
                                <th>{t('budget.col_remaining')}</th>
                                <th>{t('budget.col_percentage')}</th>
                            </tr></thead>
                            <tbody>
                                {ccBudgets.map(b => {
                                    const pct = b.amount ? ((b.spent || 0) / b.amount * 100) : 0;
                                    return (
                                        <tr key={b.id}>
                                            <td className="font-medium">{b.cost_center_name || `#${b.cost_center_id}`}</td>
                                            <td>{b.budget_name || `#${b.budget_id}`}</td>
                                            <td>{formatNumber(b.amount)} {currency}</td>
                                            <td>{formatNumber(b.spent || 0)} {currency}</td>
                                            <td className={(b.amount - (b.spent || 0)) >= 0 ? 'text-success' : 'text-danger'}>{formatNumber(b.amount - (b.spent || 0))} {currency}</td>
                                            <td>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                    <div style={{ width: 60, height: 6, background: '#e5e7eb', borderRadius: 3 }}>
                                                        <div style={{ width: `${Math.min(pct, 100)}%`, height: '100%', background: pct > 90 ? '#ef4444' : pct > 70 ? '#f59e0b' : '#22c55e', borderRadius: 3 }} />
                                                    </div>
                                                    <span className="text-xs">{pct.toFixed(0)}%</span>
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })}
                                {ccBudgets.length === 0 && <tr><td colSpan="6" className="text-center text-muted p-4">{t('budget.no_data')}</td></tr>}
                            </tbody>
                        </table>
                    </div>
                ) : activeTab === 'multiyear' ? (
                    <div className="data-table-container">
                        <table className="data-table">
                            <thead><tr>
                                <th>{t('budget.col_name')}</th>
                                <th>{t('budget.col_start_year')}</th>
                                <th>{t('budget.col_end_year')}</th>
                                <th>{t('budget.col_annual_amount')}</th>
                                <th>{t('budget.col_total')}</th>
                            </tr></thead>
                            <tbody>
                                {multiYear.map(m => (
                                    <tr key={m.id}>
                                        <td className="font-medium">{m.name}</td>
                                        <td>{m.start_year}</td>
                                        <td>{m.end_year}</td>
                                        <td>{formatNumber(m.annual_amount)} {currency}</td>
                                        <td className="font-bold">{formatNumber(m.annual_amount * ((m.end_year - m.start_year) + 1))} {currency}</td>
                                    </tr>
                                ))}
                                {multiYear.length === 0 && <tr><td colSpan="5" className="text-center text-muted p-4">{t('budget.no_data')}</td></tr>}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    /* Comparison Tab */
                    <div className="p-4">
                        <div className="d-flex gap-3 align-items-end mb-4">
                            <div className="form-group" style={{ flex: 1 }}><label className="form-label">{t('budget.budget_1_id')}</label>
                                <input type="number" className="form-input" value={compForm.budget_id_1} onChange={e => setCompForm({ ...compForm, budget_id_1: e.target.value })} /></div>
                            <div className="form-group" style={{ flex: 1 }}><label className="form-label">{t('budget.budget_2_id')}</label>
                                <input type="number" className="form-input" value={compForm.budget_id_2} onChange={e => setCompForm({ ...compForm, budget_id_2: e.target.value })} /></div>
                            <button className="btn btn-primary" onClick={handleCompare}><GitCompareArrows size={16} /> {t('budget.compare')}</button>
                        </div>
                        {comparison && (
                            <div className="data-table-container">
                                <table className="data-table">
                                    <thead><tr>
                                        <th>{t('budget.col_item')}</th>
                                        <th>{t('budget.col_budget_1')}</th>
                                        <th>{t('budget.col_budget_2')}</th>
                                        <th>{t('budget.col_difference')}</th>
                                    </tr></thead>
                                    <tbody>
                                        {(comparison.items || []).map((item, i) => {
                                            const diff = (item.budget_2_amount || 0) - (item.budget_1_amount || 0);
                                            return (
                                                <tr key={i}>
                                                    <td className="font-medium">{item.account_name || item.label || `Item ${i + 1}`}</td>
                                                    <td>{formatNumber(item.budget_1_amount)} {currency}</td>
                                                    <td>{formatNumber(item.budget_2_amount)} {currency}</td>
                                                    <td className={diff >= 0 ? 'text-success' : 'text-danger'}>{diff >= 0 ? '+' : ''}{formatNumber(diff)} {currency}</td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        )}
                        {!comparison && <div className="text-center text-muted p-6">{t('budget.select_two_to_compare')}</div>}
                    </div>
                )}
            </div>

            {/* Cost Center Budget Modal */}
            {showModal && activeTab === 'costcenter' && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 420 }}>
                        <h3 className="modal-title">{t('budget.cc_budget_modal')}</h3>
                        <form onSubmit={handleCreateCC} className="space-y-4">
                            <div className="form-group"><label className="form-label">{t('budget.col_cost_center')}</label>
                                <input type="number" className="form-input" required value={ccForm.cost_center_id} onChange={e => setCcForm({ ...ccForm, cost_center_id: e.target.value })} /></div>
                            <div className="form-group"><label className="form-label">{t('budget.col_budget')}</label>
                                <input type="number" className="form-input" required value={ccForm.budget_id} onChange={e => setCcForm({ ...ccForm, budget_id: e.target.value })} /></div>
                            <div className="form-group"><label className="form-label">{t('budget.amount')}</label>
                                <input type="number" step="0.01" className="form-input" required value={ccForm.amount} onChange={e => setCcForm({ ...ccForm, amount: e.target.value })} /></div>
                            <div className="d-flex gap-3 pt-3"><button type="submit" className="btn btn-primary flex-1">{t('budget.create')}</button>
                                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>{t('budget.cancel')}</button></div>
                        </form>
                    </div>
                </div>
            )}

            {/* Multi-Year Budget Modal */}
            {showModal && activeTab === 'multiyear' && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 420 }}>
                        <h3 className="modal-title">{t('budget.multi_year_modal')}</h3>
                        <form onSubmit={handleCreateMY} className="space-y-4">
                            <div className="form-group"><label className="form-label">{t('budget.col_name')}</label>
                                <input className="form-input" required value={myForm.name} onChange={e => setMyForm({ ...myForm, name: e.target.value })} /></div>
                            <div className="grid grid-cols-2 gap-3">
                                <div className="form-group"><label className="form-label">{t('budget.col_start_year')}</label>
                                    <input type="number" className="form-input" required value={myForm.start_year} onChange={e => setMyForm({ ...myForm, start_year: e.target.value })} /></div>
                                <div className="form-group"><label className="form-label">{t('budget.col_end_year')}</label>
                                    <input type="number" className="form-input" required value={myForm.end_year} onChange={e => setMyForm({ ...myForm, end_year: e.target.value })} /></div>
                            </div>
                            <div className="form-group"><label className="form-label">{t('budget.col_annual_amount')}</label>
                                <input type="number" step="0.01" className="form-input" required value={myForm.annual_amount} onChange={e => setMyForm({ ...myForm, annual_amount: e.target.value })} /></div>
                            <div className="d-flex gap-3 pt-3"><button type="submit" className="btn btn-primary flex-1">{t('budget.create')}</button>
                                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>{t('budget.cancel')}</button></div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default BudgetAdvanced;
