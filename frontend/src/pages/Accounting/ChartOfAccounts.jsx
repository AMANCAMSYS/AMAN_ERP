import { useEffect, useState } from 'react'
import { accountingAPI, companiesAPI } from '../../utils/api'
import { hasPermission } from '../../utils/auth'
import { useTranslation } from 'react-i18next'
import { Plus, Edit2, Trash2, ChevronRight, ChevronDown, Folder, FileText, AlertCircle, Save, X } from 'lucide-react'
import { useBranch } from '../../context/BranchContext'
import { formatNumber } from '../../utils/format'
import CurrencySelector from '../../components/common/CurrencySelector'
import { toastEmitter } from '../../utils/toastEmitter'
import BackButton from '../../components/common/BackButton';

function ChartOfAccounts() {
    const { t } = useTranslation()
    const { currentBranch, loading: branchLoading } = useBranch()
    const [accounts, setAccounts] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [currency, setCurrency] = useState('')

    // Modal & Form State
    const [modal, setModal] = useState({ open: false, type: 'create', node: null })
    const [form, setForm] = useState({
        name: '',
        name_en: '',
        account_number: '',
        account_code: '',
        account_type: 'asset',
        parent_id: null,
        currency: ''
    })

    const fetchAccounts = async () => {
        if (branchLoading) return

        try {
            setLoading(true)
            const userStr = localStorage.getItem('user')
            const user = userStr ? JSON.parse(userStr) : null
            const companyId = user?.company_id || localStorage.getItem('company_id')

            const [accountsRes, companyRes] = await Promise.all([
                accountingAPI.list({ branch_id: currentBranch?.id }),
                companyId ? companiesAPI.getCurrentCompany(companyId) : Promise.resolve({ data: { currency: '' } })
            ])

            setAccounts(accountsRes.data)
            if (companyRes.data && companyRes.data.currency) {
                setCurrency(companyRes.data.currency)
            }
        } catch (err) {
            setError(t('accounting.coa.errors.fetch_failed'))
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchAccounts()
    }, [currentBranch, branchLoading])

    const suggestNextNumber = (node) => {
        if (!node) return ''

        // Find all direct children
        const children = accounts.filter(a => a.parent_id === node.id)

        if (children.length === 0) {
            // Default to appending '01' if first child
            // But we should be smart: if parent is 1 digit (e.g. 5), maybe user likes 2 digits (51).
            // Let's stick to standard 01 padding for safety unless user manually overrides.
            return `${node.account_number}01`
        }

        // Find max account number among children
        let maxNum = 0
        children.forEach(child => {
            // Parse integer, assuming numeric
            const num = parseInt(child.account_number, 10)
            if (!isNaN(num) && num > maxNum) {
                maxNum = num
            }
        })

        if (maxNum > 0) {
            const nextNum = maxNum + 1
            return nextNum.toString()
        }

        return `${node.account_number}01`
    }

    const handleOpenModal = (type, node = null) => {
        if (type === 'create') {
            setForm({
                name: '',
                name_en: '',
                account_number: node ? suggestNextNumber(node) : '',
                account_code: '',
                account_type: node ? node.account_type : 'asset',
                parent_id: node ? node.id : null,
                currency: node?.currency || currency
            })
        } else if (type === 'edit') {
            setForm({
                name: node.name,
                name_en: node.name_en || '',
                account_number: node.account_number,
                account_code: node.account_code || '',
                account_type: node.account_type,
                parent_id: node.parent_id,
                currency: node.currency || currency
            })
        }
        setModal({ open: true, type, node })
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        try {
            if (modal.type === 'create') {
                await accountingAPI.create(form)
            } else {
                await accountingAPI.update(modal.node.id, form)
            }
            setModal({ open: false, type: 'create', node: null })
            fetchAccounts()
        } catch (err) {
            toastEmitter.emit(err.response?.data?.detail || t('common.error'), 'error')
        }
    }

    const handleDelete = async (id) => {
        try {
            await accountingAPI.delete(id)
            setModal({ ...modal, open: false })
            fetchAccounts()
        } catch (err) {
            toastEmitter.emit(err.response?.data?.detail || t('common.error'), 'error')
        }
    }

    const buildTree = (list) => {
        const tree = []
        const mapped = {}

        list.forEach(item => {
            mapped[item.id] = { ...item, children: [] }
        })

        list.forEach(item => {
            if (item.parent_id) {
                if (mapped[item.parent_id]) {
                    mapped[item.parent_id].children.push(mapped[item.id])
                }
            } else {
                tree.push(mapped[item.id])
            }
        })
        return tree
    }

    const AccountNode = ({ node, level = 0 }) => {
        const [expanded, setExpanded] = useState(true)
        const hasChildren = node.children && node.children.length > 0

        return (
            <div className="account-node-wrapper">
                <div className={`account-tree-row ${level === 0 ? 'top-level' : ''}`}>
                    <div className="row-main" onClick={() => setExpanded(!expanded)}>
                        <div className="indent" style={{ width: `${level * 24}px` }} />
                        <span className="expand-icon">
                            {hasChildren ? (expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />) : <span style={{ width: 14 }} />}
                        </span>
                        <span className="type-icon">
                            {hasChildren ? <Folder size={16} className="text-primary" /> : <FileText size={16} className="text-secondary" />}
                        </span>
                        <span className="node-number">{node.account_number}</span>
                        <span className="node-name">{node.name}</span>
                    </div>

                    <div className="row-type">
                        <span className="node-type-badge">{t(`accounting.coa.types.${node.account_type}`)}</span>
                    </div>

                    <div className="row-balance">
                        <div className="balance-main">
                            <span className="balance-amount">{formatNumber(node.balance)}</span>
                            <span className="balance-currency">{currency}</span>
                        </div>
                        {node.currency && node.currency !== currency && (
                            <div className="balance-subtext" title="Original Currency Balance">
                                <span className="sub-amount">{formatNumber(node.balance_currency || 0)}</span>
                                <span className="sub-currency">{node.currency}</span>
                            </div>
                        )}
                    </div>

                    <div className="row-actions">
                        {hasPermission('accounting.edit') && (
                            <>
                                <button className="action-btn add" title={t("accounting.coa.add_sub")} onClick={(e) => { e.stopPropagation(); handleOpenModal('create', node); }}>
                                    <Plus size={14} />
                                </button>
                                <button className="action-btn edit" title={t("common.edit")} onClick={(e) => { e.stopPropagation(); handleOpenModal('edit', node); }}>
                                    <Edit2 size={14} />
                                </button>
                            </>
                        )}
                        {hasPermission('accounting.manage') && !hasChildren && (
                            <button className="action-btn delete" title={t("common.delete")} onClick={(e) => { e.stopPropagation(); handleOpenModal('delete', node); }}>
                                <Trash2 size={14} />
                            </button>
                        )}
                    </div>
                </div>
                {expanded && hasChildren && (
                    <div className="node-children">
                        {node.children.map(child => (
                            <AccountNode key={child.id} node={child} level={level + 1} />
                        ))}
                    </div>
                )}
            </div>
        )
    }

    if (loading && accounts.length === 0) return <div className="page-center"><span className="loading"></span></div>

    const accountTree = buildTree(accounts)

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">{t('accounting.coa.title')}</h1>
                    <p className="workspace-subtitle">{t('accounting.coa.subtitle')}</p>
                </div>
                <div className="header-actions">
                    {hasPermission('accounting.edit') && (
                        <button className="btn btn-primary" onClick={() => handleOpenModal('create')}>
                            <Plus size={18} style={{ marginLeft: '8px' }} />
                            {t('accounting.coa.add_main_account')}
                        </button>
                    )}
                </div>
            </div>

            <div className="section-card no-padding">
                <div className="coa-tree-header">
                    <div className="col-name">{t('accounting.coa.table.name')}</div>
                    <div className="col-type">{t('accounting.coa.table.type')}</div>
                    <div className="col-balance">{t('accounting.coa.table.balance')}</div>
                    <div className="col-actions">{t('common.actions')}</div>
                </div>

                {error && <div className="alert alert-error m-4">{error}</div>}

                <div className="coa-tree-body">
                    {accountTree.length > 0 ? (
                        accountTree.map(node => (
                            <AccountNode key={node.id} node={node} />
                        ))
                    ) : (
                        <div className="empty-state">
                            <AlertCircle size={48} />
                            <p>{t("accounting.coa.no_accounts")}</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Account Modal */}
            {modal.open && (
                <div className="modal-overlay">
                    <div className="modal-content card slide-up" style={{ maxWidth: '500px' }}>
                        <div className="modal-header">
                            <h3>
                                {modal.type === 'create' && t('accounting.coa.new_account')}
                                {modal.type === 'edit' && `${t('common.edit')}: ${modal.node?.account_number}`}
                                {modal.type === 'delete' && t('common.delete')}
                            </h3>
                            <button className="close-btn" onClick={() => setModal({ ...modal, open: false })}><X /></button>
                        </div>

                        {modal.type === 'delete' ? (
                            <div className="p-6">
                                <div className="flex flex-col items-center text-center p-4">
                                    <AlertCircle size={48} className="text-danger mb-4" />
                                    <p className="text-lg font-bold mb-2">{t('accounting.coa.confirm_delete')}</p>
                                    <p className="text-secondary">
                                        {modal.node?.account_number} - {modal.node?.name}
                                    </p>
                                </div>
                                <div className="modal-footer mt-6" style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
                                    <button type="button" className="btn btn-secondary" onClick={() => setModal({ ...modal, open: false })}>{t('common.cancel')}</button>
                                    <button type="button" className="btn btn-danger" onClick={() => handleDelete(modal.node.id)}>
                                        <Trash2 size={18} style={{ marginLeft: '8px' }} />
                                        {t('common.delete')}
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmit} className="p-6">
                                <div className="form-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
                                    <div className="form-group">
                                        <label>{t('accounting.coa.table.name')} (Ar)</label>
                                        <input
                                            type="text"
                                            className="input"
                                            required
                                            value={form.name}
                                            onChange={e => setForm({ ...form, name: e.target.value })}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>{t('accounting.coa.table.name')} (En)</label>
                                        <input
                                            type="text"
                                            className="input"
                                            value={form.name_en}
                                            onChange={e => setForm({ ...form, name_en: e.target.value })}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>{t('accounting.coa.table.code')}</label>
                                        <input
                                            type="text"
                                            className="input"
                                            required
                                            value={form.account_number}
                                            onChange={e => setForm({ ...form, account_number: e.target.value })}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>Account Code (Optional)</label>
                                        <input
                                            type="text"
                                            className="input"
                                            value={form.account_code}
                                            onChange={e => setForm({ ...form, account_code: e.target.value })}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>{t('accounting.coa.table.type')}</label>
                                        <select
                                            className="input"
                                            value={form.account_type}
                                            onChange={e => setForm({ ...form, account_type: e.target.value })}
                                            disabled={form.parent_id !== null}
                                        >
                                            <option value="asset">{t('accounting.coa.types.asset')}</option>
                                            <option value="liability">{t('accounting.coa.types.liability')}</option>
                                            <option value="equity">{t('accounting.coa.types.equity')}</option>
                                            <option value="revenue">{t('accounting.coa.types.revenue')}</option>
                                            <option value="expense">{t('accounting.coa.types.expense')}</option>
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <CurrencySelector
                                            label={t('common.currency')}
                                            value={form.currency}
                                            onChange={(code) => setForm({ ...form, currency: code })}
                                        />
                                    </div>
                                </div>

                                <div className="modal-footer mt-6" style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                                    <button type="button" className="btn btn-secondary" onClick={() => setModal({ ...modal, open: false })}>{t('common.cancel')}</button>
                                    <button type="submit" className="btn btn-primary">
                                        <Save size={18} style={{ marginLeft: '8px' }} />
                                        {t('common.save')}
                                    </button>
                                </div>
                            </form>
                        )}
                    </div>
                </div>
            )}

            <style>{`
                .coa-tree-header {
                    display: grid;
                    grid-template-columns: 1fr 120px 150px 120px;
                    padding: 12px 24px;
                    background: var(--bg-main);
                    border-bottom: 1px solid var(--border-color);
                    font-weight: bold;
                    font-size: 13px;
                    color: var(--text-secondary);
                }
                .account-tree-row {
                    display: grid;
                    grid-template-columns: 1fr 120px 150px 120px;
                    align-items: center;
                    padding: 8px 12px;
                    border-bottom: 1px solid rgba(0,0,0,0.03);
                    transition: all 0.2s;
                }
                .account-tree-row:hover {
                    background: rgba(37, 99, 235, 0.05);
                }
                .account-tree-row.top-level {
                    font-weight: 600;
                    margin-top: 4px;
                }
                .row-main {
                    display: flex;
                    align-items: center;
                    cursor: pointer;
                }
                .expand-icon {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    width: 24px;
                    color: var(--text-secondary);
                }
                .type-icon {
                    margin: 0 8px;
                }
                .node-number {
                    color: var(--primary);
                    font-family: monospace;
                    margin-left: 12px;
                    font-weight: 600;
                }
                .node-name {
                    flex: 1;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
                .node-type-badge {
                    font-size: 11px;
                    background: #f1f5f9;
                    padding: 2px 8px;
                    border-radius: 4px;
                    color: var(--text-secondary);
                }
                .row-balance {
                    display: flex;
                    flex-direction: column;
                    align-items: flex-end;
                    justify-content: center;
                    gap: 0;
                }
                .balance-main {
                    display: flex;
                    align-items: baseline;
                    gap: 4px;
                    font-weight: bold;
                }
                .balance-currency {
                    font-size: 10px;
                    color: var(--text-secondary);
                }
                .balance-subtext {
                    font-size: 11px;
                    color: #059669; /* Greenish for clarity */
                    font-weight: 500;
                    display: flex;
                    align-items: baseline;
                    gap: 4px;
                }
                .sub-currency {
                    font-size: 9px;
                    opacity: 0.8;
                }
                .row-actions {
                    display: flex;
                    gap: 4px;
                    justify-content: flex-end;
                    opacity: 0;
                    transition: opacity 0.2s;
                }
                .account-tree-row:hover .row-actions {
                    opacity: 1;
                }
                .action-btn {
                    width: 28px;
                    height: 28px;
                    border-radius: 6px;
                    border: none;
                    background: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    transition: all 0.2s;
                }
                .action-btn.add:hover { color: var(--success); background: #ecfdf5; }
                .action-btn.edit:hover { color: var(--primary); background: #eff6ff; }
                .action-btn.delete:hover { color: var(--danger); background: #fef2f2; }
                
                .modal-overlay {
                    position: fixed;
                    top: 0; left: 0; right: 0; bottom: 0;
                    background: rgba(0,0,0,0.5);
                    backdrop-filter: blur(4px);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                }
                .modal-header {
                    padding: 20px 24px;
                    border-bottom: 1px solid var(--border-color);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .close-btn {
                    background: none;
                    border: none;
                    cursor: pointer;
                    color: var(--text-secondary);
                }
                .empty-state {
                    padding: 80px;
                    text-align: center;
                    color: var(--text-secondary);
                }
            `}</style>
        </div>
    )
}

export default ChartOfAccounts
