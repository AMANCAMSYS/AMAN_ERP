import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { purchasesAPI } from '../../utils/api'
import { useTranslation } from 'react-i18next'
import { formatShortDate } from '../../utils/dateUtils'
import DataTable from '../../components/common/DataTable'
import SearchFilter from '../../components/common/SearchFilter'
import BackButton from '../../components/common/BackButton'

const STATUS_COLORS = {
  matched: 'badge-success',
  held: 'badge-warning',
  approved_with_exception: 'badge-info',
  rejected: 'badge-danger',
}

export default function MatchList() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  useEffect(() => {
    loadMatches()
  }, [statusFilter])

  const loadMatches = async () => {
    try {
      setLoading(true)
      const params = {}
      if (statusFilter) params.status = statusFilter
      const res = await purchasesAPI.listMatches(params)
      setMatches(Array.isArray(res.data) ? res.data : [])
    } catch (err) {
      setError(t('common.error_loading'))
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const filtered = useMemo(() => {
    if (!search) return matches
    const q = search.toLowerCase()
    return matches.filter(m =>
      (m.po_number || '').toLowerCase().includes(q) ||
      (m.invoice_number || '').toLowerCase().includes(q) ||
      (m.supplier_name || '').toLowerCase().includes(q)
    )
  }, [matches, search])

  const columns = [
    { key: 'id', label: '#', style: { width: '60px' } },
    { key: 'po_number', label: t('matching.po_number'), style: { fontWeight: 'bold' } },
    { key: 'invoice_number', label: t('matching.invoice_number') },
    { key: 'supplier_name', label: t('matching.supplier') },
    {
      key: 'match_status',
      label: t('matching.status'),
      render: (val) => (
        <span className={`badge ${STATUS_COLORS[val] || 'badge-secondary'}`}>
          {t(`matching.status_${val}`, val)}
        </span>
      ),
    },
    {
      key: 'matched_at',
      label: t('matching.matched_at'),
      render: (val) => val ? formatShortDate(val) : '—',
    },
  ]

  return (
    <div className="workspace fade-in">
      <div className="workspace-header">
        <BackButton />
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 className="workspace-title">{t('matching.title')}</h1>
            <p className="workspace-subtitle">{t('matching.subtitle')}</p>
          </div>
          <button className="btn btn-outline" onClick={() => navigate('/buying/matching/tolerances')}>
            ⚙ {t('matching.tolerances')}
          </button>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <SearchFilter
        value={search}
        onChange={setSearch}
        placeholder={t('matching.search_placeholder')}
        filters={[{
          key: 'status',
          label: t('matching.status'),
          options: [
            { value: 'matched', label: t('matching.status_matched') },
            { value: 'held', label: t('matching.status_held') },
            { value: 'approved_with_exception', label: t('matching.status_approved_with_exception') },
            { value: 'rejected', label: t('matching.status_rejected') },
          ],
        }]}
        filterValues={{ status: statusFilter }}
        onFilterChange={(key, val) => setStatusFilter(val)}
      />

      <DataTable
        columns={columns}
        data={filtered}
        loading={loading}
        onRowClick={(row) => navigate(`/buying/matching/${row.id}`)}
        emptyTitle={t('matching.no_matches')}
        emptyDesc={t('matching.empty_desc')}
      />
    </div>
  )
}
