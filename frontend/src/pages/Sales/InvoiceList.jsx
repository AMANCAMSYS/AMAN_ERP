import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { salesAPI } from '../../utils/api'
import { useTranslation } from 'react-i18next'
import { formatShortDate } from '../../utils/dateUtils'
import { useBranch } from '../../context/BranchContext'
import { formatNumber } from '../../utils/format'
import Pagination, { usePagination } from '../../components/common/Pagination'

function InvoiceList() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { currentBranch } = useBranch()
    const [invoices, setInvoices] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        const fetchInvoices = async () => {
            try {
                setLoading(true)
                const response = await salesAPI.listInvoices({ branch_id: currentBranch?.id })
                setInvoices(response.data)
            } catch (err) {
                setError(t('common.error_loading') || 'فشل في تحميل الفواتير')
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
                        <h1 className="workspace-title">{t('sales.invoices.title')}</h1>
                        <p className="workspace-subtitle">{t('sales.invoices.subtitle')}</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => navigate('/sales/invoices/new')}>
                        + {t('sales.invoices.create_new')}
                    </button>
                </div>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <div className="card card-flush" style={{ overflow: 'hidden' }}>
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>{t('sales.invoices.table.number')}</th>
                            <th>{t('sales.invoices.table.customer')}</th>
                            <th>{t('sales.invoices.table.date')}</th>
                            <th>{t('sales.invoices.table.total')}</th>
                            <th>{t('sales.invoices.table.status')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {invoices.length === 0 ? (
                            <tr>
                                <td colSpan="5" className="start-guide">
                                    <div style={{ padding: '40px', textAlign: 'center' }}>
                                        <h3>{t('sales.invoices.no_invoices')}</h3>
                                        <p>{t('sales.invoices.empty_desc')}</p>
                                        <button className="btn btn-primary mt-4" onClick={() => navigate('/sales/invoices/new')}>
                                            {t('sales.invoices.create_btn')}
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ) : (
                            paginatedItems.map(invoice => (
                                <tr key={invoice.id} onClick={() => navigate(`/sales/invoices/${invoice.id}`)} style={{ cursor: 'pointer' }}>
                                    <td style={{ fontWeight: 'bold' }}>{invoice.invoice_number}</td>
                                    <td>{invoice.customer_name}</td>
                                    <td>{formatShortDate(invoice.invoice_date)}</td>
                                    <td style={{ fontWeight: 'bold' }}>{formatNumber(invoice.total)}</td>
                                    <td>
                                        <span className={`badge ${invoice.status === 'paid' ? 'badge-success' :
                                            invoice.status === 'partial' ? 'badge-warning' :
                                                'badge-danger'
                                            }`}>
                                            {invoice.status === 'paid' ? t('sales.invoices.status.paid') :
                                                invoice.status === 'partial' ? t('sales.invoices.status.partial') :
                                                    t('sales.invoices.status.unpaid')}
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

export default InvoiceList
