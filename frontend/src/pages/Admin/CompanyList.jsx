import { useEffect, useState, useMemo } from 'react'
import { companiesAPI } from '../../utils/api'
import { ChevronLeft, ChevronRight, Info } from 'lucide-react'
import { useTranslation } from 'react-i18next';
import { formatShortDate } from '../../utils/dateUtils';
import BackButton from '../../components/common/BackButton';
import DataTable from '../../components/common/DataTable';
import SearchFilter from '../../components/common/SearchFilter';


function CompanyList() {
    const { t } = useTranslation();
    const [companies, setCompanies] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [total, setTotal] = useState(0)
    const [page, setPage] = useState(1)
    const [search, setSearch] = useState('')
    const [filterValues, setFilterValues] = useState({})
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

    const filteredCompanies = useMemo(() => {
        let result = companies;
        if (filterValues.status) {
            result = result.filter(c => c.status === filterValues.status);
        }
        return result;
    }, [companies, filterValues]);

    const columns = useMemo(() => [
        {
            key: 'id',
            label: t('admin.companies.id'),
            render: (val) => (
                <span style={{ fontWeight: 'bold', color: 'var(--primary)' }}>{val}</span>
            ),
        },
        {
            key: 'company_name',
            label: t('admin.companies.name'),
        },
        {
            key: 'database_name',
            label: t('admin.companies.database'),
            render: (val) => (
                <code style={{ background: '#f1f5f9', padding: '2px 6px', borderRadius: '4px' }}>
                    {val}
                </code>
            ),
        },
        {
            key: 'email',
            label: t('admin.companies.email'),
        },
        {
            key: 'status',
            label: t('common.status_title'),
            render: (val) => (
                <span className={`badge badge-${val === 'active' ? 'success' : 'warning'}`}>
                    {val === 'active' ? t('common.active') : t('common.disabled')}
                </span>
            ),
        },
        {
            key: 'plan_type',
            label: t('admin.companies.plan'),
        },
        {
            key: 'created_at',
            label: t('admin.companies.reg_date'),
            render: (val) => formatShortDate(val),
        },
    ], [t]);

    const filters = useMemo(() => [
        {
            key: 'status',
            label: t('common.status_title'),
            options: [
                { value: 'active', label: t('common.active') },
                { value: 'disabled', label: t('common.disabled') },
            ],
        },
    ], [t]);

    return (
        <div className="workspace">
            <div className="workspace-header">
                <BackButton />
                <div>
                    <h1 className="workspace-title">{t('admin.companies.title')}</h1>
                    <p className="workspace-subtitle">{t('admin.companies.subtitle')}</p>
                </div>
            </div>

            {error && <div className="alert alert-error mb-4">{error}</div>}

            <SearchFilter
                value={search}
                onChange={(val) => { setSearch(val); setPage(1); }}
                placeholder={t('common.search')}
                filters={filters}
                filterValues={filterValues}
                onFilterChange={(key, value) => setFilterValues(prev => ({ ...prev, [key]: value }))}
            />

            <DataTable
                columns={columns}
                data={filteredCompanies}
                loading={loading}
                emptyTitle={t('admin.companies.no_companies')}
                rowKey="id"
                paginate={false}
            />

            {/* Server-side pagination */}
            {total > 0 && (
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
            )}
        </div>
    )
}

export default CompanyList
