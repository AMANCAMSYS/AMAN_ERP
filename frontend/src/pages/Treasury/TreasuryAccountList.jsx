import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { treasuryAPI } from '../../utils/api'
import { getCurrency } from '../../utils/auth'
import { useTranslation } from 'react-i18next'
import { useBranch } from '../../context/BranchContext'
import { currenciesAPI } from '../../utils/api'
import SimpleModal from '../../components/common/SimpleModal'
import { toastEmitter } from '../../utils/toastEmitter'
import DataTable from '../../components/common/DataTable'
import SearchFilter from '../../components/common/SearchFilter'
import BackButton from '../../components/common/BackButton'

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
    const [search, setSearch] = useState('')
    const [typeFilter, setTypeFilter] = useState('')
    const [accountForm, setAccountForm] = useState({
        name: '', name_en: '', account_type: 'cash', currency: '',
        bank_name: '', account_number: '', iban: '', branch_id: '',
        opening_balance: 0, exchange_rate: 1, allow_overdraft: false
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
                opening_balance: 0, exchange_rate: 1, allow_overdraft: false
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
            exchange_rate: 1,
            allow_overdraft: account.allow_overdraft || false
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
                branch_id: currentBranch?.id || null,
                allow_overdraft: accountForm.allow_overdraft
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

    const filteredAccounts = useMemo(() => {
        let result = accounts
        if (search) {
            const q = search.toLowerCase()
            result = result.filter(acc =>
                (acc.name || '').toLowerCase().includes(q) ||
                (acc.name_en || '').toLowerCase().includes(q) ||
                (acc.bank_name || '').toLowerCase().includes(q)
            )
        }
        if (typeFilter) {
            result = result.filter(acc => acc.account_type === typeFilter)
        }
        return result
    }, [accounts, search, typeFilter])

    const columns = [
        {
            key: 'name',
            label: t('common.name'),
            width: '40%',
            render: (val, row) => (
                <div>
                    <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{val}</div>
                    {row.bank_name && <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{row.bank_name} - {row.account_number}</div>}
                </div>
            ),
        },
        {
            key: 'account_type',
            label: t('treasury.account_type'),
            width: '20%',
            render: (val) => (
                <span className={`badge ${val === 'bank' ? 'badge-info' : 'badge-success'}`}>
                    {val === 'bank' ? t('treasury.bank_name') : t('treasury.cash_box')}
                </span>
            ),
        },
        {
            key: 'current_balance',
            label: t('treasury.current_balance'),
            width: '20%',
            render: (val, row) => (
                <div style={{ fontWeight: '600', direction: 'ltr', textAlign: 'right' }}>
                    {row.currency && row.currency !== baseCurrency ? (
                        <>
                            <div>{Number(row.balance_in_currency || 0).toLocaleString()} {row.currency}</div>
                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                                {Number(val).toLocaleString()} {baseCurrency}
                            </div>
                        </>
                    ) : (
                        <div>{Number(val).toLocaleString()} {row.currency || baseCurrency}</div>
                    )}
                </div>
            ),
        },
        {
            key: '_actions',
            label: t('common.actions'),
            width: '20%',
            render: (_, row) => (
                <div onClick={(e) => e.stopPropagation()}>
                    <button className="btn btn-link" onClick={() => navigate(`/treasury/accounts/${row.id}`)}>
                        {t('common.view_details')}
                    </button>
                    <button
                        className="btn-icon"
                        onClick={() => handleEditClick(row)}
                        title={t('common.edit')}
                        style={{ marginRight: '8px' }}
                    >
                        {'\u270F\uFE0F'}
                    </button>
                    <button
                        className="btn-icon"
                        onClick={() => handleDeleteClick(row)}
                        title={t('common.delete')}
                        style={{ color: 'var(--danger)' }}
                    >
                        {'\uD83D\uDDD1\uFE0F'}
                    </button>
                </div>
            ),
        },
    ]

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
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

            <SearchFilter
                value={search}
                onChange={setSearch}
                placeholder={t('treasury.search_placeholder', '\u0628\u062D\u062B \u0628\u0627\u0633\u0645 \u0627\u0644\u062D\u0633\u0627\u0628...')}
                filters={[{
                    key: 'type',
                    label: t('treasury.account_type'),
                    options: [
                        { value: 'cash', label: t('treasury.cash_box') },
                        { value: 'bank', label: t('treasury.bank_name') },
                    ],
                }]}
                filterValues={{ type: typeFilter }}
                onFilterChange={(key, val) => setTypeFilter(val)}
            />

            <DataTable
                columns={columns}
                data={filteredAccounts}
                loading={loading}
                emptyIcon={'\uD83C\uDFE6'}
                emptyTitle={t('treasury.no_accounts')}
                emptyAction={{ label: t('common.add_new'), onClick: () => setShowAdd(true) }}
            />

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
                    <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <input
                            type="checkbox"
                            id="edit_allow_overdraft"
                            checked={accountForm.allow_overdraft}
                            onChange={e => setAccountForm({ ...accountForm, allow_overdraft: e.target.checked })}
                        />
                        <label htmlFor="edit_allow_overdraft" className="form-label" style={{ margin: 0 }}>{t('treasury.allow_overdraft', 'السماح بالسحب على المكشوف')}</label>
                    </div>
                </div>
            </SimpleModal>

            {/* Delete Confirmation Modal */}
            {showDelete && (
                <div className="modal-overlay" onClick={() => setShowDelete(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '450px' }}>
                        <div className="modal-header">
                            <h2 style={{ color: 'var(--danger)' }}>{'\u26A0\uFE0F'} {t('common.confirm_delete')}</h2>
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
