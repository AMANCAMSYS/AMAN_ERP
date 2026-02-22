import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { inventoryAPI, companiesAPI } from '../../utils/api'
import { useTranslation } from 'react-i18next'
import { useBranch } from '../../context/BranchContext'
import Pagination, { usePagination } from '../../components/common/Pagination'

import { formatShortDate, formatDateTime } from '../../utils/dateUtils';
import BackButton from '../../components/common/BackButton';

function SupplierList() {
    const { t, i18n } = useTranslation()
    const navigate = useNavigate()
    const { currentBranch } = useBranch()
    const [suppliers, setSuppliers] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [currency, setCurrency] = useState('')

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Fetch suppliers and company currency
                setLoading(true)
                const userStr = localStorage.getItem('user')
                const user = userStr ? JSON.parse(userStr) : null
                const companyId = user?.company_id || localStorage.getItem('company_id')

                const [suppliersRes, companyRes] = await Promise.all([
                    inventoryAPI.listSuppliers({ branch_id: currentBranch?.id }),
                    companyId ? companiesAPI.getCurrentCompany(companyId) : Promise.resolve({ data: { currency: '' } })
                ])

                setSuppliers(suppliersRes.data)
                if (companyRes.data && companyRes.data.currency) {
                    setCurrency(companyRes.data.currency)
                }
            } catch (err) {
                setError(t('common.error_loading'))
                console.error(err)
            } finally {
                setLoading(false)
            }
        }
        fetchData()
    }, [t, currentBranch])

    const { currentPage, pageSize, totalItems, paginatedItems, onPageChange, onPageSizeChange } = usePagination(suppliers)

    if (loading) return <div className="page-center"><span className="loading"></span></div>

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className="workspace-title">{t('buying.suppliers.title')}</h1>
                        <p className="workspace-subtitle">{t('buying.suppliers.subtitle')}</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => navigate('/buying/suppliers/new')}>
                        <span style={{ marginLeft: '8px' }}>+</span>
                        {t('buying.suppliers.new_supplier')}
                    </button>
                </div>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <div className="data-table-container">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th style={{ width: '12%' }}>{t('buying.suppliers.table.code')}</th>
                            <th style={{ width: '28%' }}>{t('buying.suppliers.table.name')}</th>
                            <th style={{ width: '20%' }}>{t('buying.suppliers.table.contact')}</th>
                            <th style={{ width: '20%' }}>{t('buying.suppliers.table.balance')}</th>
                            <th style={{ width: '15%' }}>{t('buying.suppliers.table.status')}</th>
                            <th style={{ width: '15%' }}>{t('buying.suppliers.table.created_at')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {suppliers.length === 0 ? (
                            <tr>
                                <td colSpan="6" className="start-guide">
                                    <div style={{ padding: '60px 20px', textAlign: 'center' }}>
                                        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🏬</div>
                                        <h3 style={{ fontSize: '18px', marginBottom: '8px' }}>{t('buying.suppliers.empty.title')}</h3>
                                        <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
                                            {t('buying.suppliers.empty.desc')}
                                        </p>
                                        <button className="btn btn-primary" onClick={() => navigate('/buying/suppliers/new')}>
                                            {t('buying.suppliers.empty.action')}
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ) : (
                            paginatedItems.map(supplier => (
                                <tr key={supplier.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/buying/suppliers/${supplier.id}`)}>
                                    <td>
                                        <span style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--primary)', fontSize: '13px', background: 'rgba(37,99,235,0.08)', padding: '2px 8px', borderRadius: '4px' }}>
                                            {supplier.party_code || '—'}
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
                                                🏢
                                            </div>
                                            <div>
                                                <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{supplier.name}</div>
                                                {supplier.name_en && (
                                                    <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                                                        {supplier.name_en}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </td>
                                    <td>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                            {supplier.phone && (
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px' }}>
                                                    <span>📞</span>
                                                    <span style={{ direction: 'ltr' }}>{supplier.phone}</span>
                                                </div>
                                            )}
                                            {supplier.email && (
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                                                    <span>✉️</span>
                                                    <span>{supplier.email}</span>
                                                </div>
                                            )}
                                            {!supplier.phone && !supplier.email && <span style={{ color: 'var(--text-muted)' }}>-</span>}
                                        </div>
                                    </td>
                                    <td>
                                        <div style={{
                                            fontWeight: '600',
                                            fontSize: '15px',
                                            color: supplier.current_balance > 0 ? 'var(--error)' : 'var(--text-primary)',
                                            direction: 'ltr',
                                            textAlign: i18n.language === 'ar' ? 'right' : 'left'
                                        }}>
                                            {supplier.current_balance.toLocaleString()} {currency}
                                        </div>
                                    </td>
                                    <td>
                                        <span className={`badge ${supplier.is_active ? 'badge-success' : 'badge-danger'}`}>
                                            {supplier.is_active ? t('common.active') : t('common.inactive')}
                                        </span>
                                    </td>
                                    <td style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                                        {formatShortDate(supplier.created_at)}
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

export default SupplierList
