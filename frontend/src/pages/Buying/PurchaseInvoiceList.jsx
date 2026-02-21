import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { purchasesAPI } from '../../utils/api'
import { useTranslation } from 'react-i18next'
import { formatShortDate } from '../../utils/dateUtils'
import { useBranch } from '../../context/BranchContext'
import { formatNumber } from '../../utils/format'
import Pagination, { usePagination } from '../../components/common/Pagination'

function PurchaseInvoiceList() {
    const { t, i18n } = useTranslation()
    const navigate = useNavigate()
    const { currentBranch } = useBranch()
    const [invoices, setInvoices] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        const fetchInvoices = async () => {
            try {
                setLoading(true)
                const response = await purchasesAPI.listInvoices({ branch_id: currentBranch?.id })
                setInvoices(response.data)
            } catch (err) {
                setError(t('common.error_loading'))
                console.error(err)
            } finally {
                setLoading(false)
            }
        }
        fetchInvoices()
    }, [currentBranch, t])

    const { currentPage, pageSize, totalItems, paginatedItems, onPageChange, onPageSizeChange } = usePagination(invoices)

    if (loading) return <div className="page-center"><span className="loading"></span></div>

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className="workspace-title">{t('buying.purchase_invoices.title')}</h1>
                        <p className="workspace-subtitle">{t('buying.purchase_invoices.subtitle')}</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => navigate('/buying/invoices/new')}>
                        <span style={{ marginLeft: '8px' }}>+</span>
                        {t('buying.purchase_invoices.new_invoice')}
                    </button>
                </div>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <div className="data-table-container">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>{t('buying.purchase_invoices.table.invoice_number')}</th>
                            <th>{t('buying.purchase_invoices.table.supplier')}</th>
                            <th>{t('buying.purchase_invoices.table.date')}</th>
                            <th>{t('buying.purchase_invoices.table.total')}</th>
                            <th>{t('buying.purchase_invoices.table.status')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {invoices.length === 0 ? (
                            <tr>
                                <td colSpan="5" className="start-guide">
                                    <div style={{ padding: '40px', textAlign: 'center' }}>
                                        <h3>{t('buying.purchase_invoices.empty.title')}</h3>
                                        <p>{t('buying.purchase_invoices.empty.desc')}</p>
                                        <button className="btn btn-primary mt-4" onClick={() => navigate('/buying/invoices/new')}>
                                            {t('buying.purchase_invoices.empty.action')}
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ) : (
                            paginatedItems.map(inv => (
                                <tr key={inv.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/buying/invoices/${inv.id}`)}>
                                    <td style={{ fontWeight: 'bold' }}>{inv.invoice_number}</td>
                                    <td>{inv.supplier_name}</td>
                                    <td>{formatShortDate(inv.invoice_date)}</td>
                                    <td>{formatNumber(inv.total)}</td>
                                    <td>
                                        <span className={`badge ${inv.status === 'paid' ? 'badge-success' : inv.status === 'partial' ? 'badge-warning' : 'badge-danger'}`}>
                                            {inv.status === 'paid' ? t('buying.purchase_invoices.details.status.paid') :
                                                inv.status === 'partial' ? t('buying.purchase_invoices.details.status.partial') :
                                                    t('buying.purchase_invoices.details.status.unpaid')}
                                        </span>
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

export default PurchaseInvoiceList
