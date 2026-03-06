import { useEffect, useState } from 'react'
import { companiesAPI } from '../../utils/api'
import { Search, ChevronLeft, ChevronRight, Info } from 'lucide-react'
import { useTranslation } from 'react-i18next';
import { formatShortDate } from '../../utils/dateUtils';
import BackButton from '../../components/common/BackButton';


function CompanyList() {
    const { t } = useTranslation();
    const [companies, setCompanies] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [total, setTotal] = useState(0)
    const [page, setPage] = useState(1)
    const [search, setSearch] = useState('')
    const limit = 20

    const fetchCompanies = async () => {
        setLoading(true)
        try {
            const skip = (page - 1) * limit
            const response = await companiesAPI.list({ skip, limit, search })
            setCompanies(response.data.companies || [])
            setTotal(response.data.total || 0)
        } catch (err) {
            setError(t('admin.companies.load_error'))
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        const delayDebounceFn = setTimeout(() => {
            fetchCompanies()
        }, 300)

        return () => clearTimeout(delayDebounceFn)
    }, [page, search])

    const totalPages = Math.ceil(total / limit)

    return (
        <div className="workspace">
            <div className="workspace-header">
                <BackButton />
                <div>
                    <h1 className="workspace-title">{t('admin.companies.title')}</h1>
                    <p className="workspace-subtitle">{t('admin.companies.subtitle')}</p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                        <input
                            type="text"
                            className="form-input pr-10 min-w-[300px]"
                            placeholder={t('common.search') || "Search companies..."}
                            value={search}
                            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                        />
                    </div>
                </div>
            </div>

            {error && <div className="alert alert-error mb-4">{error}</div>}

            <div className="card">
                <div className="table-container">
                    <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                            <tr style={{ textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>
                                <th style={{ padding: '12px' }}>{t('admin.companies.id')}</th>
                                <th style={{ padding: '12px' }}>{t('admin.companies.name')}</th>
                                <th style={{ padding: '12px' }}>{t('admin.companies.database')}</th>
                                <th style={{ padding: '12px' }}>{t('admin.companies.email')}</th>
                                <th style={{ padding: '12px' }}>{t('common.status_title')}</th>
                                <th style={{ padding: '12px' }}>{t('admin.companies.plan')}</th>
                                <th style={{ padding: '12px' }}>{t('admin.companies.reg_date')}</th>
                            </tr>
                        </thead>
                        <tbody className={loading ? 'opacity-50' : ''}>
                            {companies.map(company => (
                                <tr key={company.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                                    <td style={{ padding: '12px', fontWeight: 'bold', color: 'var(--primary)' }}>
                                        {company.id}
                                    </td>
                                    <td style={{ padding: '12px' }}>{company.company_name}</td>
                                    <td style={{ padding: '12px' }}>
                                        <code style={{ background: '#f1f5f9', padding: '2px 6px', borderRadius: '4px' }}>
                                            {company.database_name}
                                        </code>
                                    </td>
                                    <td style={{ padding: '12px' }}>{company.email}</td>
                                    <td style={{ padding: '12px' }}>
                                        <span className={`badge badge-${company.status === 'active' ? 'success' : 'warning'}`}>
                                            {company.status === 'active' ? t('common.active') : t('common.disabled')}
                                        </span>
                                    </td>
                                    <td style={{ padding: '12px' }}>{company.plan_type}</td>
                                    <td style={{ padding: '12px' }}>
                                        {formatShortDate(company.created_at)}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {companies.length === 0 && !loading && (
                    <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
                        {t('admin.companies.no_companies')}
                    </div>
                )}

                {/* Pagination footer */}
                <div className="flex items-center justify-between mt-6 p-4 border-t border-slate-100">
                    <div className="text-sm text-slate-500">
                        {t('common.showing') || "Showing"} {Math.min(total, (page - 1) * limit + 1)} - {Math.min(total, page * limit)} {t('common.of') || "of"} {total}
                    </div>
                    <div className="flex gap-2">
                        <button
                            className="btn btn-secondary p-2"
                            disabled={page === 1 || loading}
                            onClick={() => setPage(page - 1)}
                        >
                            <ChevronLeft size={20} />
                        </button>
                        <div className="flex items-center px-4 font-bold text-slate-700">
                            {page} / {totalPages || 1}
                        </div>
                        <button
                            className="btn btn-secondary p-2"
                            disabled={page >= totalPages || loading}
                            onClick={() => setPage(page + 1)}
                        >
                            <ChevronRight size={20} />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default CompanyList
