import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Save, Search } from 'lucide-react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { budgetsAPI, accountingAPI } from '../../utils/api';
import { getCurrency } from '../../utils/auth';
import BackButton from '../../components/common/BackButton';

const BudgetItems = () => {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    const { id } = useParams();

    const [loading, setLoading] = useState(true);
    const [accounts, setAccounts] = useState([]);
    const [budgetItems, setBudgetItems] = useState({}); // { account_id: { planned, notes } }
    const [searchTerm, setSearchTerm] = useState('');
    const [saving, setSaving] = useState(false);
    const currency = getCurrency() || '';

    useEffect(() => {
        fetchData();
    }, [id]);

    const fetchData = async () => {
        setLoading(true);
        try {
            // Fetch Accounts
            const accountsRes = await accountingAPI.list();
            // Filter only Expenses and Revenues (usually what we budget for)
            // But maybe assets too for Capex? Let's check type.
            const allAccounts = accountsRes.data || [];
            const budgetableAccounts = allAccounts.filter(a => ['expense', 'revenue', 'asset'].includes(a.account_type));
            setAccounts(budgetableAccounts);

            // Fetch Existing Items (via Report endpoint or we need a specific getItems?)
            // The report endpoint returns planned amounts. Let's use that for now to populate.
            const reportRes = await budgetsAPI.getReport(id);
            const itemsMap = {};
            (reportRes.data || []).forEach(item => {
                itemsMap[item.account_id] = {
                    planned: item.planned,
                    notes: '' // Report doesn't return notes currently, need to update API if we want notes
                };
            });
            setBudgetItems(itemsMap);

        } catch (error) {
            console.error(error);
            toast.error(t('common.error_loading'));
        } finally {
            setLoading(false);
        }
    };

    const handleAmountChange = (accountId, field, value) => {
        const floatValue = parseFloat(value) || 0;
        setBudgetItems(prev => {
            const currentItem = prev[accountId] || { planned: 0, notes: '' };
            if (field === 'monthly') {
                return {
                    ...prev,
                    [accountId]: {
                        ...currentItem,
                        planned: floatValue * 12,
                        monthly: floatValue
                    }
                };
            } else {
                return {
                    ...prev,
                    [accountId]: {
                        ...currentItem,
                        planned: floatValue,
                        monthly: floatValue / 12
                    }
                };
            }
        });
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            const items = Object.entries(budgetItems)
                .filter(([_, val]) => val.planned > 0)
                .map(([accountId, val]) => ({
                    account_id: parseInt(accountId),
                    planned_amount: val.planned,
                    notes: val.notes || ''
                }));

            if (items.length === 0) {
                toast.error(t('accounting.budgets.no_items'));
                return;
            }

            await budgetsAPI.setItems(id, items);
            toast.success(t('accounting.budgets.items_saved'));
        } catch (error) {
            console.error(error);
            toast.error(t('common.error_saving'));
        } finally {
            setSaving(false);
        }
    };

    const filteredAccounts = accounts.filter(acc =>
        acc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        acc.account_number.includes(searchTerm)
    );

    return (
        <div className="workspace fade-in">
            <div className="workspace-header mb-4">
                <div className="d-flex align-items-center gap-3">
                        <BackButton />
                    <div>
                        <h1 className="workspace-title mb-0">{t('accounting.budgets.items', 'Budget Items')}</h1>
                    </div>
                </div>
                <div className="header-actions">
                    <button onClick={handleSave} className="btn btn-primary shadow-sm" disabled={saving}>
                        <Save size={18} className="me-2" />
                        {saving ? t('common.saving') : t('common.save')}
                    </button>
                </div>
            </div>

            <div className="card card-flush shadow-sm">
                <div className="card-header border-0 pt-4 pb-2">
                    <div className="search-box w-100 max-w-400px">
                        <div className="input-group input-group-solid">
                            <span className="input-group-text"><Search size={18} className="text-gray-500" /></span>
                            <input
                                type="text"
                                className="form-input"
                                placeholder={t('common.search')}
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                autoComplete="off"
                            />
                        </div>
                    </div>
                </div>
                <div className="card-body p-0">
                    <div className="data-table-container">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th className="ps-4">{t('accounting.account_number')}</th>
                                    <th>{t('accounting.account_name')}</th>
                                    <th>{t('accounting.account_type')}</th>
                                    <th width="180" className="text-center">{t('accounting.budgets.monthly_amount', 'Monthly Amount')} <span className="text-muted small">({currency})</span></th>
                                    <th width="180" className="text-center">{t('accounting.budgets.planned_amount', 'Annual Amount')} <span className="text-muted small">({currency})</span></th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    <tr><td colSpan="5" className="text-center p-8">
                                        <div className="spinner-border spinner-border-sm text-primary me-2"></div>
                                        {t('common.loading')}
                                    </td></tr>
                                ) : filteredAccounts.length === 0 ? (
                                    <tr><td colSpan="5" className="text-center p-8 text-muted">{t('common.no_data')}</td></tr>
                                ) : (
                                    filteredAccounts.map((acc) => (
                                        <tr key={acc.id}>
                                            <td className="ps-4">
                                                <code className="text-primary fw-medium">{acc.account_number}</code>
                                            </td>
                                            <td>
                                                <div className="fw-bold text-gray-800">{acc.name}</div>
                                            </td>
                                            <td>
                                                <span className={`badge badge-light-${acc.account_type === 'expense' ? 'danger' : acc.account_type === 'revenue' ? 'success' : 'primary'} fw-bold`}>
                                                    {t(`accounting.coa.types.${acc.account_type}`) || acc.account_type}
                                                </span>
                                            </td>
                                            <td>
                                                <div className="input-group input-group-sm input-group-solid">
                                                    <input
                                                        type="number"
                                                        className="form-input text-center"
                                                        value={budgetItems[acc.id]?.monthly || (budgetItems[acc.id]?.planned / 12) || ''}
                                                        onChange={(e) => handleAmountChange(acc.id, 'monthly', e.target.value)}
                                                        placeholder="0.00"
                                                        autoComplete="off"
                                                    />
                                                </div>
                                            </td>
                                            <td>
                                                <div className="input-group input-group-sm input-group-solid">
                                                    <input
                                                        type="number"
                                                        className="form-input text-center fw-bold text-primary"
                                                        value={budgetItems[acc.id]?.planned || ''}
                                                        onChange={(e) => handleAmountChange(acc.id, 'annual', e.target.value)}
                                                        placeholder="0.00"
                                                        autoComplete="off"
                                                    />
                                                </div>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default BudgetItems;
