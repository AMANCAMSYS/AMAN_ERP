import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { treasuryAPI } from '../../utils/api'
import { getCurrency } from '../../utils/auth'
import { useTranslation } from 'react-i18next'
import { useBranch } from '../../context/BranchContext'
import { currenciesAPI } from '../../utils/api'
import SimpleModal from '../../components/common/SimpleModal'
import { toastEmitter } from '../../utils/toastEmitter'

export default function TreasuryAccountList() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { currentBranch } = useBranch()
    const [accounts, setAccounts] = useState([])
    const [baseCurrency] = useState(getCurrency() || '')
    const [currencies, setCurrencies] = useState([])
    const [loading, setLoading] = useState(true)
    const [showAdd, setShowAdd] = useState(false)
    const [showEdit, setShowEdit] = useState(false)
    const [showDelete, setShowDelete] = useState(false)
    const [selectedAccount, setSelectedAccount] = useState(null)
    const [accountForm, setAccountForm] = useState({
        name: '', name_en: '', account_type: 'cash', currency: '',
        bank_name: '', account_number: '', iban: '', branch_id: '',
        opening_balance: 0, exchange_rate: 1
    })

    const fetchAccounts = async () => {
        try {
            setLoading(true)
            const response = await treasuryAPI.listAccounts(currentBranch?.id)
            setAccounts(response.data)
        } catch (err) {
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchAccounts()
        fetchCurrencies()
    }, [currentBranch])

    const fetchCurrencies = async () => {
        try {
            const response = await currenciesAPI.list()
            setCurrencies(response.data)
            // Set default currency if not set
            if (!accountForm.currency && response.data.length > 0) {
                const defaultCurr = response.data.find(c => c.is_base) || response.data[0]
                setAccountForm(prev => ({
                    ...prev,
                    currency: defaultCurr.code,
                    exchange_rate: defaultCurr.current_rate || 1
                }))
            }
        } catch (error) {
            console.error('Error fetching currencies:', error)
        }
    }

    const handleCreate = async () => {
        try {
            await treasuryAPI.createAccount({
                ...accountForm,
                branch_id: currentBranch?.id || null
            })
            toastEmitter.emit(t('treasury.success_create_account'), 'success')
            setShowAdd(false)
            fetchAccounts()
            setAccountForm({
                name: '', name_en: '', account_type: 'cash', currency: baseCurrency,
                bank_name: '', account_number: '', iban: '', branch_id: '',
                opening_balance: 0, exchange_rate: 1
            })
        } catch (err) {
            console.error(err)
        }
    }

    const handleEditClick = (account) => {
        setSelectedAccount(account)
        setAccountForm({
            name: account.name || '',
            name_en: account.name_en || '',
            account_type: account.account_type || 'cash',
            currency: account.currency || baseCurrency,
            bank_name: account.bank_name || '',
            account_number: account.account_number || '',
            iban: account.iban || '',
            branch_id: account.branch_id || '',
            opening_balance: 0,
            exchange_rate: 1
        })
        setShowEdit(true)
    }

    const handleUpdate = async () => {
        try {
            const updateData = {
                name: accountForm.name,
                name_en: accountForm.name_en,
                account_type: accountForm.account_type,
                currency: accountForm.currency,
                bank_name: accountForm.bank_name,
                account_number: accountForm.account_number,
                iban: accountForm.iban,
                branch_id: currentBranch?.id || null
            }
            await treasuryAPI.updateAccount(selectedAccount.id, updateData)
            toastEmitter.emit(t('treasury.success_update_account'), 'success')
            setShowEdit(false)
            setSelectedAccount(null)
            fetchAccounts()
        } catch (err) {
            const errorMsg = err.response?.data?.detail || t('common.error_saving')
            toastEmitter.emit(errorMsg, 'error')
        }
    }

    const handleDeleteClick = (account) => {
        setSelectedAccount(account)
        setShowDelete(true)
    }

    const handleDelete = async () => {
        try {
            await treasuryAPI.deleteAccount(selectedAccount.id)
            toastEmitter.emit(t('treasury.success_delete_account'), 'success')
            setShowDelete(false)
            setSelectedAccount(null)
            fetchAccounts()
        } catch (err) {
            const errorMsg = err.response?.data?.detail || t('common.error_deleting')
            toastEmitter.emit(errorMsg, 'error')
        }
    }

    if (loading) return <div className="page-center"><span className="loading"></span></div>

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className="workspace-title">{t('treasury.menu.accounts')}</h1>
                        <p className="workspace-subtitle">{t('treasury.subtitle')}</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => setShowAdd(true)}>
                        <span style={{ marginLeft: '8px' }}>+</span>
                        {t('common.add_new')}
                    </button>
                </div>
            </div>

            <div className="data-table-container">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th style={{ width: '40%' }}>{t('common.name')}</th>
                            <th style={{ width: '20%' }}>{t('treasury.account_type')}</th>
                            <th style={{ width: '20%' }}>{t('treasury.current_balance')}</th>
                            <th style={{ width: '20%' }}>{t('common.actions')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {accounts.length === 0 ? (
                            <tr>
                                <td colSpan="4" className="start-guide">
                                    <div style={{ padding: '60px 20px', textAlign: 'center' }}>
                                        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🏦</div>
                                        <h3 style={{ fontSize: '18px', marginBottom: '8px' }}>{t('treasury.no_accounts')}</h3>
                                        <button className="btn btn-primary" onClick={() => setShowAdd(true)}>
                                            {t('common.add_new')}
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ) : (
                            accounts.map(acc => (
                                <tr key={acc.id}>
                                    <td>
                                        <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{acc.name}</div>
                                        {acc.bank_name && <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{acc.bank_name} - {acc.account_number}</div>}
                                    </td>
                                    <td>
                                        <span className={`badge ${acc.account_type === 'bank' ? 'badge-info' : 'badge-success'}`}>
                                            {acc.account_type === 'bank' ? t('treasury.bank_name') : t('treasury.cash_box')}
                                        </span>
                                    </td>
                                    <td>
                                        <div style={{ fontWeight: '600', direction: 'ltr', textAlign: 'right' }}>
                                            {acc.currency && acc.currency !== baseCurrency ? (
                                                <>
                                                    <div>{Number(acc.balance_in_currency || 0).toLocaleString()} {acc.currency}</div>
                                                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                                                        {Number(acc.current_balance).toLocaleString()} {baseCurrency}
                                                    </div>
                                                </>
                                            ) : (
                                                <div>{Number(acc.current_balance).toLocaleString()} {acc.currency || baseCurrency}</div>
                                            )}
                                        </div>
                                    </td>
                                    <td>
                                        <button className="btn btn-link" onClick={() => navigate(`/treasury/accounts/${acc.id}`)}>
                                            {t('common.view_details')}
                                        </button>
                                        <button
                                            className="btn-icon"
                                            onClick={() => handleEditClick(acc)}
                                            title={t('common.edit')}
                                            style={{ marginRight: '8px' }}
                                        >
                                            ✏️
                                        </button>
                                        <button
                                            className="btn-icon"
                                            onClick={() => handleDeleteClick(acc)}
                                            title={t('common.delete')}
                                            style={{ color: 'var(--danger)' }}
                                        >
                                            🗑️
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            <SimpleModal
                isOpen={showAdd}
                onClose={() => setShowAdd(false)}
                title={t('treasury.add_account')}
                footer={
                    <>
                        <button className="btn btn-secondary" onClick={() => setShowAdd(false)}>{t('common.cancel')}</button>
                        <button className="btn btn-primary" onClick={handleCreate}>{t('common.save')}</button>
                    </>
                }
            >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div className="form-group">
                        <label className="form-label">{t('treasury.account_type')}</label>
                        <select className="form-input" value={accountForm.account_type} onChange={e => setAccountForm({ ...accountForm, account_type: e.target.value })}>
                            <option value="cash">{t('treasury.cash_box')}</option>
                            <option value="bank">{t('treasury.bank_name')}</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label className="form-label">{t('common.currency')}</label>
                        <select
                            className="form-input"
                            value={accountForm.currency}
                            onChange={e => {
                                const code = e.target.value;
                                const curr = currencies.find(c => c.code === code);
                                setAccountForm({
                                    ...accountForm,
                                    currency: code,
                                    exchange_rate: curr?.current_rate || 1
                                });
                            }}
                        >
                            {currencies.map(c => (
                                <option key={c.code} value={c.code}>{c.code} - {c.name}</option>
                            ))}
                        </select>
                    </div>

                    {accountForm.currency && accountForm.currency !== baseCurrency && (
                        <div className="form-group">
                            <label className="form-label">{t('common.exchange_rate')}</label>
                            <input
                                type="number"
                                className="form-input"
                                value={accountForm.exchange_rate}
                                onChange={e => setAccountForm({ ...accountForm, exchange_rate: parseFloat(e.target.value) || 1 })}
                                step="0.000001"
                            />
                            <div className="form-text text-sm text-gray-500">
                                1 {accountForm.currency} = {accountForm.exchange_rate} {baseCurrency}
                            </div>
                        </div>
                    )}

                    <div className="form-group">
                        <label className="form-label">{t('common.name')}</label>
                        <input className="form-input" value={accountForm.name} onChange={e => setAccountForm({ ...accountForm, name: e.target.value })} />
                    </div>
                    <div className="form-group">
                        <label className="form-label">{t('treasury.opening_balance')}</label>
                        <input
                            type="number"
                            className="form-input"
                            value={accountForm.opening_balance}
                            onChange={e => setAccountForm({ ...accountForm, opening_balance: parseFloat(e.target.value) || 0 })}
                        />
                        {accountForm.currency && accountForm.currency !== baseCurrency && (
                            <div className="form-text text-sm text-gray-500 mt-1">
                                {t('common.equivalent')}: {(accountForm.opening_balance * (accountForm.exchange_rate || 1)).toLocaleString()} {baseCurrency}
                            </div>
                        )}
                    </div>
                    {accountForm.account_type === 'bank' && (
                        <>
                            <div className="form-row">
                                <div className="form-group" style={{ flex: 1 }}>
                                    <label className="form-label">{t('treasury.bank_name')}</label>
                                    <input className="form-input" value={accountForm.bank_name} onChange={e => setAccountForm({ ...accountForm, bank_name: e.target.value })} />
                                </div>
                                <div className="form-group" style={{ flex: 1 }}>
                                    <label className="form-label">IBAN</label>
                                    <input className="form-input" value={accountForm.iban} onChange={e => setAccountForm({ ...accountForm, iban: e.target.value })} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('treasury.account_number')}</label>
                                <input className="form-input" value={accountForm.account_number} onChange={e => setAccountForm({ ...accountForm, account_number: e.target.value })} />
                            </div>
                        </>
                    )}
                </div>
            </SimpleModal>

            {/* Edit Modal */}
            <SimpleModal
                isOpen={showEdit}
                onClose={() => setShowEdit(false)}
                title={t('treasury.edit_account')}
                footer={
                    <>
                        <button className="btn btn-secondary" onClick={() => setShowEdit(false)}>{t('common.cancel')}</button>
                        <button className="btn btn-primary" onClick={handleUpdate}>{t('common.save')}</button>
                    </>
                }
            >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div className="form-group">
                        <label className="form-label">{t('treasury.account_type')}</label>
                        <select className="form-input" value={accountForm.account_type} onChange={e => setAccountForm({ ...accountForm, account_type: e.target.value })}>
                            <option value="cash">{t('treasury.cash_box')}</option>
                            <option value="bank">{t('treasury.bank_name')}</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label className="form-label">{t('common.currency')}</label>
                        <select
                            className="form-input"
                            value={accountForm.currency}
                            onChange={e => {
                                const code = e.target.value;
                                const curr = currencies.find(c => c.code === code);
                                setAccountForm({
                                    ...accountForm,
                                    currency: code,
                                    exchange_rate: curr?.current_rate || 1
                                });
                            }}
                        >
                            {currencies.map(c => (
                                <option key={c.code} value={c.code}>{c.code} - {c.name}</option>
                            ))}
                        </select>
                    </div>
                    <div className="form-group">
                        <label className="form-label">{t('common.name')}</label>
                        <input className="form-input" value={accountForm.name} onChange={e => setAccountForm({ ...accountForm, name: e.target.value })} />
                    </div>
                    <div className="form-group">
                        <label className="form-label">{t('common.name_en')}</label>
                        <input className="form-input" value={accountForm.name_en} onChange={e => setAccountForm({ ...accountForm, name_en: e.target.value })} />
                    </div>
                    {accountForm.account_type === 'bank' && (
                        <>
                            <div className="form-row">
                                <div className="form-group" style={{ flex: 1 }}>
                                    <label className="form-label">{t('treasury.bank_name')}</label>
                                    <input className="form-input" value={accountForm.bank_name} onChange={e => setAccountForm({ ...accountForm, bank_name: e.target.value })} />
                                </div>
                                <div className="form-group" style={{ flex: 1 }}>
                                    <label className="form-label">IBAN</label>
                                    <input className="form-input" value={accountForm.iban} onChange={e => setAccountForm({ ...accountForm, iban: e.target.value })} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('treasury.account_number')}</label>
                                <input className="form-input" value={accountForm.account_number} onChange={e => setAccountForm({ ...accountForm, account_number: e.target.value })} />
                            </div>
                        </>
                    )}
                </div>
            </SimpleModal>

            {/* Delete Confirmation Modal */}
            {showDelete && (
                <div className="modal-overlay" onClick={() => setShowDelete(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '450px' }}>
                        <div className="modal-header">
                            <h2 style={{ color: 'var(--danger)' }}>⚠️ {t('common.confirm_delete')}</h2>
                            <button onClick={() => setShowDelete(false)} className="close-btn">&times;</button>
                        </div>
                        <div style={{ padding: '1rem 0' }}>
                            <p>{t('treasury.delete_account_confirm', { name: selectedAccount?.name })}</p>
                            <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '8px' }}>
                                {t('common.action_cannot_be_undone')}
                            </p>
                        </div>
                        <div className="modal-actions" style={{ marginTop: '1.5rem' }}>
                            <button onClick={() => setShowDelete(false)} className="btn btn-secondary">
                                {t('common.cancel')}
                            </button>
                            <button onClick={handleDelete} className="btn btn-danger">
                                {t('common.delete')}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <style>{`
                .modal-overlay {
                    position: fixed;
                    top: 0; left: 0; right: 0; bottom: 0;
                    background: rgba(0,0,0,0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                }
                .modal-content {
                    background: white;
                    padding: 1.5rem;
                    border-radius: 12px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                }
                .modal-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 1rem;
                }
                .close-btn {
                    background: none;
                    border: none;
                    font-size: 1.5rem;
                    cursor: pointer;
                    color: var(--text-secondary);
                }
                .modal-actions {
                    display: flex;
                    justify-content: flex-end;
                    gap: 0.75rem;
                }
                .btn-danger {
                    background-color: var(--danger);
                    color: white;
                    border: none;
                    padding: 0.5rem 1.5rem;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 500;
                }
                .btn-danger:hover {
                    opacity: 0.9;
                }
            `}</style>
        </div>
    )
}

