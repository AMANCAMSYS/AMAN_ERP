import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { salesAPI } from '../../utils/api'
import { getCurrency } from '../../utils/auth'
import { useTranslation } from 'react-i18next'
import { formatNumber } from '../../utils/format'
import { useBranch } from '../../context/BranchContext'
import Pagination, { usePagination } from '../../components/common/Pagination'
import { formatShortDate } from '../../utils/dateUtils';


function CustomerList() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { currentBranch } = useBranch()
    const [customers, setCustomers] = useState([])
    const [currency] = useState(getCurrency())
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        const fetchCustomers = async () => {
            try {
                setLoading(true)
                const response = await salesAPI.listCustomers({ branch_id: currentBranch?.id })
                setCustomers(response.data)
            } catch (err) {
                setError(t('common.error_loading'))
                console.error(err)
            } finally {
                setLoading(false)
            }
        }
        fetchCustomers()
    }, [currentBranch, t])

    const { currentPage, pageSize, totalItems, paginatedItems, onPageChange, onPageSizeChange } = usePagination(customers)

    if (loading) return <div className="page-center"><span className="loading"></span></div>

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className="workspace-title">{t('sales.customers.title')}</h1>
                        <p className="workspace-subtitle">{t('sales.customers.subtitle')}</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => navigate('/sales/customers/new')}>
                        <span style={{ marginLeft: '8px' }}>+</span>
                        {t('sales.customers.add_new')}
                    </button>
                </div>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <div className="data-table-container">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th style={{ width: '12%' }}>{t('sales.customers.table.code')}</th>
                            <th style={{ width: '28%' }}>{t('sales.customers.table.name')}</th>
                            <th style={{ width: '20%' }}>{t('sales.customers.table.contact')}</th>
                            <th style={{ width: '20%' }}>{t('sales.customers.table.balance')}</th>
                            <th style={{ width: '15%' }}>{t('sales.customers.table.status')}</th>
                            <th style={{ width: '15%' }}>{t('sales.customers.table.added_date')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {customers.length === 0 ? (
                            <tr>
                                <td colSpan="6" className="start-guide">
                                    <div style={{ padding: '60px 20px', textAlign: 'center' }}>
                                        <div style={{ fontSize: '48px', marginBottom: '16px' }}>👥</div>
                                        <h3 style={{ fontSize: '18px', marginBottom: '8px' }}>{t('sales.customers.no_customers')}</h3>
                                        <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
                                            {t('sales.customers.empty_state_desc')}
                                        </p>
                                        <button className="btn btn-primary" onClick={() => navigate('/sales/customers/new')}>
                                            {t('sales.customers.add_first')}
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ) : (
                            paginatedItems.map(customer => (
                                <tr key={customer.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/sales/customers/${customer.id}`)}>
                                    <td>
                                        <span style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--primary)', fontSize: '13px', background: 'rgba(37,99,235,0.08)', padding: '2px 8px', borderRadius: '4px' }}>
                                            {customer.party_code || '—'}
                                        </span>
                                    </td>
                                    <td>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                            <div style={{
                                                width: '36px', height: '36px',
                                                borderRadius: '50%', background: 'var(--bg-hover)',
                                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                fontSize: '18px'
                                            }}>
                                                👤
                                            </div>
                                            <div>
                                                <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{customer.name}</div>
                                                {customer.name_en && (
                                                    <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                                                        {customer.name_en}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </td>
                                    <td>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                            {customer.phone && (
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px' }}>
                                                    <span>📞</span>
                                                    <span style={{ direction: 'ltr' }}>{customer.phone}</span>
                                                </div>
                                            )}
                                            {customer.email && (
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                                                    <span>✉️</span>
                                                    <span>{customer.email}</span>
                                                </div>
                                            )}
                                            {!customer.phone && !customer.email && <span style={{ color: 'var(--text-muted)' }}>-</span>}
                                        </div>
                                    </td>
                                    <td>
                                        <div style={{
                                            fontWeight: '600',
                                            fontSize: '15px',
                                            color: customer.current_balance > 0 ? 'var(--error)' : 'var(--text-primary)',
                                            direction: 'ltr',
                                            textAlign: 'right'
                                        }}>
                                            {formatNumber(customer.current_balance)} {currency}
                                        </div>
                                    </td>
                                    <td>
                                        <span className={`badge ${customer.is_active ? 'badge-success' : 'badge-danger'}`}>
                                            {customer.is_active ? t('sales.customers.status.active') : t('sales.customers.status.inactive')}
                                        </span>
                                    </td>
                                    <td style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                                        {formatShortDate(customer.created_at)}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
                <Pagination currentPage={currentPage} totalItems={totalItems} pageSize={pageSize} onPageChange={onPageChange} onPageSizeChange={onPageSizeChange} />
            </div>
        </div>
    )
}

export default CustomerList
