import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { contractsAPI } from '../../utils/api'
import { useTranslation } from 'react-i18next'
import { formatShortDate } from '../../utils/dateUtils'
import { useBranch } from '../../context/BranchContext'
import { formatNumber } from '../../utils/format'

function ContractList() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { currentBranch } = useBranch()
    const [contracts, setContracts] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        const fetchContracts = async () => {
            try {
                setLoading(true)
                const response = await contractsAPI.listContracts({ branch_id: currentBranch?.id })
                setContracts(response.data)
            } catch (err) {
                setError(t('common.error_loading'))
                console.error(err)
            } finally {
                setLoading(false)
            }
        }
        fetchContracts()
    }, [currentBranch, t])

    if (loading) return <div className="page-center"><span className="loading"></span></div>

    const getStatusBadge = (status) => {
        switch (status) {
            case 'active': return 'badge-success'
            case 'expired': return 'badge-danger'
            case 'cancelled': return 'badge-ghost'
            default: return 'badge-info'
        }
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className="workspace-title">{t('sales.contracts.title')}</h1>
                        <p className="workspace-subtitle">{t('sales.contracts.subtitle')}</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => navigate('/sales/contracts/new')}>
                        + {t('sales.contracts.create_new')}
                    </button>
                </div>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <div className="card card-flush" style={{ overflow: 'hidden' }}>
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>{t('sales.contracts.table.number')}</th>
                            <th>{t('sales.contracts.table.customer')}</th>
                            <th>{t('sales.contracts.table.type')}</th>
                            <th>{t('sales.contracts.table.start_date')}</th>
                            <th>{t('sales.contracts.table.total')}</th>
                            <th>{t('sales.contracts.table.status')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {contracts.length === 0 ? (
                            <tr>
                                <td colSpan="6" className="start-guide">
                                    <div style={{ padding: '40px', textAlign: 'center' }}>
                                        <h3>{t('sales.contracts.no_contracts')}</h3>
                                        <p>{t('sales.contracts.empty_desc')}</p>
                                        <button className="btn btn-primary mt-4" onClick={() => navigate('/sales/contracts/new')}>
                                            {t('sales.contracts.create_btn')}
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ) : (
                            contracts.map(contract => (
                                <tr key={contract.id} onClick={() => navigate(`/sales/contracts/${contract.id}`)} style={{ cursor: 'pointer' }}>
                                    <td style={{ fontWeight: 'bold' }}>{contract.contract_number}</td>
                                    <td>{contract.party_name}</td>
                                    <td>{contract.contract_type === 'subscription' ? t('sales.contracts.subscription') : t('sales.contracts.fixed')}</td>
                                    <td>{formatShortDate(contract.start_date)}</td>
                                    <td style={{ fontWeight: 'bold' }}>{formatNumber(contract.total_amount)}</td>
                                    <td>
                                        <span className={`badge ${getStatusBadge(contract.status)}`}>
                                            {contract.status}
                                        </span>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    )
}

export default ContractList
