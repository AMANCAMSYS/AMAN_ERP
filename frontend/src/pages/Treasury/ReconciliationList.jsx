import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Plus, Landmark, Trash2, CheckCircle, Clock, FileText } from 'lucide-react';
import { treasuryAPI, reconciliationAPI } from '../../utils/api';
import { useBranch } from '../../context/BranchContext';
import { toastEmitter } from '../../utils/toastEmitter';
import BackButton from '../../components/common/BackButton';

const ReconciliationList = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const navigate = useNavigate();
    const { currentBranch } = useBranch();

    const [accounts, setAccounts] = useState([]);
    const [selectedAccount, setSelectedAccount] = useState('');
    const [reconciliations, setReconciliations] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchAccounts = async () => {
            try {
                const branchId = currentBranch?.id || null;
                const res = await treasuryAPI.listAccounts(branchId);
                const banks = res.data.filter(a => a.account_type === 'bank');
                setAccounts(banks);
                if (banks.length > 0 && !selectedAccount) setSelectedAccount(String(banks[0].id));
            } catch (error) {
                console.error("Failed to fetch accounts", error);
            }
        };
        fetchAccounts();
    }, [currentBranch]);

    useEffect(() => {
        if (selectedAccount) {
            fetchReconciliations(selectedAccount);
        }
    }, [selectedAccount, currentBranch]);

    const fetchReconciliations = async (accountId) => {
        try {
            setLoading(true);
            const res = await reconciliationAPI.list({ account_id: accountId });
            setReconciliations(res.data);
        } catch (error) {
            console.error("Failed to fetch reconciliations", error);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (e, recId) => {
        e.stopPropagation();
        if (!window.confirm(t('common.confirm_delete'))) return;
        try {
            await reconciliationAPI.delete(recId);
            toastEmitter.emit(t('common.deleted_successfully'), 'success');
            fetchReconciliations(selectedAccount);
        } catch (error) {
            toastEmitter.emit(error.response?.data?.detail || t('common.error'), 'error');
        }
    };

    const getProgressBar = (matched, total) => {
        if (total === 0) return null;
        const pct = Math.round((matched / total) * 100);
        return (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ 
                    width: '80px', height: '6px', borderRadius: '3px', 
                    backgroundColor: 'var(--border-color)', overflow: 'hidden' 
                }}>
                    <div style={{ 
                        width: `${pct}%`, height: '100%', borderRadius: '3px',
                        backgroundColor: pct === 100 ? 'var(--success)' : 'var(--primary)',
                        transition: 'width 0.3s ease'
                    }} />
                </div>
                <span className="small text-muted">{matched}/{total}</span>
            </div>
        );
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="d-flex justify-content-between align-items-center">
                    <div>
                        <h1 className="workspace-title">{t('treasury.reconciliation.title')}</h1>
                        <p className="workspace-subtitle">{t('treasury.reconciliation.subtitle')}</p>
                    </div>
                    <button
                        className="btn btn-primary d-flex align-items-center gap-2"
                        onClick={() => navigate('/treasury/reconciliation/new')}
                    >
                        <Plus size={18} />
                        {t('treasury.reconciliation.new')}
                    </button>
                </div>
            </div>

            <div className="card mb-4 p-4">
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div style={{
                        width: '40px', height: '40px', borderRadius: '10px',
                        backgroundColor: 'var(--bg-hover)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        color: 'var(--primary)'
                    }}>
                        <Landmark size={20} />
                    </div>
                    <div style={{ flex: 1, maxWidth: '400px' }}>
                        <select
                            className="form-input"
                            value={selectedAccount}
                            onChange={(e) => setSelectedAccount(e.target.value)}
                        >
                            <option value="">{t('treasury.reconciliation.select_account')}</option>
                            {accounts.map(acc => (
                                <option key={acc.id} value={String(acc.id)}>{acc.name} ({acc.currency})</option>
                            ))}
                        </select>
                    </div>
                </div>
            </div>

            <div className="data-table-container">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>{t('common.date')}</th>
                            <th>{t('treasury.reconciliation.status')}</th>
                            <th>{t('treasury.reconciliation.start_bal')}</th>
                            <th>{t('treasury.reconciliation.end_bal')}</th>
                            <th>{t('treasury.reconciliation.progress')}</th>
                            <th>{t('common.created_by')}</th>
                            <th style={{ width: '60px' }}></th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr>
                                <td colSpan="8" className="text-center py-5">
                                    <div className="spinner-border text-primary spinner-border-sm" role="status"></div>
                                </td>
                            </tr>
                        ) : reconciliations.length === 0 ? (
                            <tr>
                                <td colSpan="8" className="text-center py-5 text-muted">
                                    <div style={{ fontSize: '48px', opacity: 0.2 }} className="mb-2">📑</div>
                                    {t('common.no_data')}
                                </td>
                            </tr>
                        ) : (
                            reconciliations.map((rec, idx) => (
                                <tr
                                    key={rec.id}
                                    style={{ cursor: 'pointer' }}
                                    onClick={() => navigate(`/treasury/reconciliation/${rec.id}`)}
                                >
                                    <td className="text-muted small">{idx + 1}</td>
                                    <td className="fw-bold text-dark">{rec.statement_date}</td>
                                    <td>
                                        <span className={`badge ${rec.status === 'posted' ? 'badge-success' : 'badge-warning'}`}
                                              style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                                            {rec.status === 'posted' 
                                                ? <><CheckCircle size={12} /> {t('treasury.reconciliation.status_posted')}</>
                                                : <><Clock size={12} /> {t('treasury.reconciliation.status_draft')}</>
                                            }
                                        </span>
                                    </td>
                                    <td className="font-monospace fw-bold">{Number(rec.start_balance).toLocaleString('en', { minimumFractionDigits: 2 })}</td>
                                    <td className="font-monospace fw-bold">{Number(rec.end_balance).toLocaleString('en', { minimumFractionDigits: 2 })}</td>
                                    <td>{getProgressBar(rec.matched_count || 0, rec.total_lines || 0)}</td>
                                    <td className="small text-muted">{rec.created_by_name || 'Admin'}</td>
                                    <td className="text-end">
                                        {rec.status === 'draft' && (
                                            <button
                                                className="btn btn-link text-danger p-0"
                                                onClick={(e) => handleDelete(e, rec.id)}
                                                title={t('common.delete')}
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default ReconciliationList;
