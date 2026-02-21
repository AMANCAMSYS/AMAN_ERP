import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { accountingAPI } from '../../utils/api'
import { useToast } from '../../context/ToastContext'
import { formatNumber } from '../../utils/format'
import { getCurrency, hasPermission } from '../../utils/auth'
import { formatDate, formatDateTime } from '../../utils/dateUtils';

function JournalEntryList() {
    const { t, i18n } = useTranslation()
    const navigate = useNavigate()
    const { showToast } = useToast()
    const currency = getCurrency()
    const isRTL = i18n.language === 'ar'
    const canCreate = hasPermission('accounting.create_journal_entry')
    const canPost = hasPermission('accounting.post_journal_entry')
    const canVoid = hasPermission('accounting.void_journal_entry')

    const [entries, setEntries] = useState([])
    const [loading, setLoading] = useState(true)
    const [total, setTotal] = useState(0)
    const [page, setPage] = useState(1)
    const [statusFilter, setStatusFilter] = useState('')
    const [search, setSearch] = useState('')
    const [selectedEntry, setSelectedEntry] = useState(null)
    const [detailLoading, setDetailLoading] = useState(false)
    const limit = 25

    const fetchEntries = useCallback(async () => {
        try {
            setLoading(true)
            const params = { page, limit }
            if (statusFilter) params.status_filter = statusFilter
            if (search) params.search = search
            const res = await accountingAPI.listJournalEntries(params)
            setEntries(res.data.items || [])
            setTotal(res.data.total || 0)
        } catch (err) {
            showToast(err.response?.data?.detail || t('common.error'), 'error')
        } finally {
            setLoading(false)
        }
    }, [page, statusFilter, search, showToast])

    useEffect(() => { fetchEntries() }, [fetchEntries])

    const handlePost = async (entryId) => {
        if (!confirm(t('accounting.journal_entries.post_this_journal_entry'))) return
        try {
            const res = await accountingAPI.postJournalEntry(entryId)
            showToast(res.data.message, 'success')
            fetchEntries()
            setSelectedEntry(null)
        } catch (err) {
            showToast(err.response?.data?.detail || t('common.error'), 'error')
        }
    }

    const handleVoid = async (entryId) => {
        if (!confirm(t('accounting.journal_entries.void_this_entry_a_reversal_entry_will_be_created'))) return
        try {
            const res = await accountingAPI.voidJournalEntry(entryId)
            showToast(res.data.message, 'success')
            fetchEntries()
            setSelectedEntry(null)
        } catch (err) {
            showToast(err.response?.data?.detail || t('common.error'), 'error')
        }
    }

    const handleViewDetail = async (entryId) => {
        try {
            setDetailLoading(true)
            const res = await accountingAPI.getJournalEntry(entryId)
            setSelectedEntry(res.data)
        } catch (err) {
            showToast(err.response?.data?.detail || t('common.error'), 'error')
        } finally {
            setDetailLoading(false)
        }
    }

    const statusBadge = (status) => {
        const map = {
            draft: { class: 'badge-warning', label: t('common.status_draft') || (t('accounting.journal_entries.draft')) },
            posted: { class: 'badge-success', label: t('common.status_posted') || (t('accounting.journal_entries.posted')) },
            voided: { class: 'badge-secondary', label: t('common.status_voided') || (t('accounting.journal_entries.voided')) },
        }
        const s = map[status] || { class: '', label: status }
        return <span className={`badge ${s.class}`}>{s.label}</span>
    }

    const totalPages = Math.ceil(total / limit)

    return (
        <div className="workspace fade-in">
            <div className="workspace-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h1 className="workspace-title">
                        {t('accounting.journal_entries.title')}
                    </h1>
                    <p className="workspace-subtitle">
                        {total} {t('accounting.journal_entries.title')}
                    </p>
                </div>
                {canCreate && (
                    <button className="btn btn-primary" onClick={() => navigate('/accounting/journal-entries/new')}>
                        + {t('accounting.journal_entries.new_entry')}
                    </button>
                )}
            </div>

            {/* Filters */}
            <div className="card mt-3 p-3" style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
                <select
                    className="form-control"
                    style={{ width: '180px' }}
                    value={statusFilter}
                    onChange={e => { setStatusFilter(e.target.value); setPage(1) }}
                >
                    <option value="">{t('common.all_status')}</option>
                    <option value="draft">{t('common.status_draft') || (t('accounting.journal_entries.draft'))}</option>
                    <option value="posted">{t('common.status_posted') || (t('accounting.journal_entries.posted'))}</option>
                    <option value="voided">{t('common.status_voided') || (t('accounting.journal_entries.voided'))}</option>
                </select>
                <input
                    type="text"
                    className="form-control"
                    style={{ width: '250px' }}
                    placeholder={t('common.search')}
                    value={search}
                    onChange={e => { setSearch(e.target.value); setPage(1) }}
                />
            </div>

            {/* Table */}
            <div className="card mt-3">
                <div className="data-table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>{t('accounting.journal_entries.table.id')}</th>
                                <th>{t('accounting.journal_entries.table.date')}</th>
                                <th>{t('accounting.journal_entries.table.description')}</th>
                                <th>{t('common.reference')}</th>
                                <th>{t('accounting.journal_entries.table.debit')}</th>
                                <th>{t('accounting.journal_entries.table.credit')}</th>
                                <th>{t('accounting.journal_entries.table.status')}</th>
                                {(canPost || canVoid) && <th>{t('accounting.journal_entries.table.actions')}</th>}
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr><td colSpan="8" style={{ textAlign: 'center', padding: '2rem' }}>
                                    {t('accounting.journal_entries.loading')}
                                </td></tr>
                            ) : entries.length === 0 ? (
                                <tr><td colSpan="8" style={{ textAlign: 'center', padding: '2rem' }}>
                                    {t('accounting.journal_entries.no_entries_found')}
                                </td></tr>
                            ) : entries.map(e => (
                                <tr key={e.id} style={{ cursor: 'pointer' }}
                                    onClick={() => handleViewDetail(e.id)}>
                                    <td><strong>{e.entry_number}</strong></td>
                                    <td>{formatDate(e.entry_date)}</td>
                                    <td style={{ maxWidth: '250px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        {e.description}
                                    </td>
                                    <td>{e.reference || '—'}</td>
                                    <td>{formatNumber(e.total_debit)}</td>
                                    <td>{formatNumber(e.total_credit)}</td>
                                    <td>{statusBadge(e.status)}</td>
                                    {(canPost || canVoid) && (
                                        <td onClick={ev => ev.stopPropagation()}>
                                            <div style={{ display: 'flex', gap: '0.25rem' }}>
                                                {e.status === 'draft' && canPost && (
                                                    <button className="btn btn-sm btn-success" onClick={() => handlePost(e.id)}>
                                                        {t('accounting.journal_entries.post')}
                                                    </button>
                                                )}
                                                {e.status === 'posted' && canVoid && (
                                                    <button className="btn btn-sm btn-danger" onClick={() => handleVoid(e.id)}>
                                                        {t('accounting.journal_entries.void')}
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    )}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                    <div style={{ display: 'flex', justifyContent: 'center', padding: '1rem', gap: '0.5rem' }}>
                        <button className="btn btn-sm btn-outline" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
                            {isRTL ? '→' : '←'}
                        </button>
                        <span style={{ padding: '0.25rem 1rem', lineHeight: '32px' }}>
                            {page} / {totalPages}
                        </span>
                        <button className="btn btn-sm btn-outline" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>
                            {isRTL ? '←' : '→'}
                        </button>
                    </div>
                )}
            </div>

            {/* Detail Modal */}
            {selectedEntry && (
                <div className="modal-overlay" onClick={() => setSelectedEntry(null)}>
                    <div className="modal-content" onClick={ev => ev.stopPropagation()} style={{ maxWidth: '800px', maxHeight: '80vh', overflow: 'auto' }}>
                        <div className="modal-header">
                            <h3>{selectedEntry.entry_number} — {statusBadge(selectedEntry.status)}</h3>
                            <button className="modal-close" onClick={() => setSelectedEntry(null)}>✕</button>
                        </div>
                        <div className="modal-body">
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1rem' }}>
                                <div><strong>{t('common.date')}:</strong> {formatDate(selectedEntry.entry_date)}</div>
                                <div><strong>{t('common.reference')}:</strong> {selectedEntry.reference || '—'}</div>
                                <div style={{ gridColumn: '1 / -1' }}><strong>{t('common.description')}:</strong> {selectedEntry.description}</div>
                                <div><strong>{t('common.currency') || (t('accounting.journal_entries.currency'))}:</strong> {selectedEntry.currency}</div>
                                <div><strong>{t('common.created_by')}:</strong> {selectedEntry.created_by_name}</div>
                            </div>

                            <table className="data-table" style={{ fontSize: '0.85rem' }}>
                                <thead>
                                    <tr>
                                        <th>{t('common.account') || (t('accounting.journal_entries.account'))}</th>
                                        <th>{t('common.description')}</th>
                                        <th>{t('accounting.journal_entries.table.debit')}</th>
                                        <th>{t('accounting.journal_entries.table.credit')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {selectedEntry.lines?.map((l, i) => (
                                        <tr key={i}>
                                            <td>{l.account_number} - {isRTL ? l.account_name : (l.account_name_en || l.account_name)}</td>
                                            <td>{l.description || '—'}</td>
                                            <td>{l.debit > 0 ? formatNumber(l.debit) : ''}</td>
                                            <td>{l.credit > 0 ? formatNumber(l.credit) : ''}</td>
                                        </tr>
                                    ))}
                                    <tr style={{ fontWeight: 'bold', borderTop: '2px solid var(--border)' }}>
                                        <td colSpan="2">{t('common.total')}</td>
                                        <td>{formatNumber(selectedEntry.lines?.reduce((s, l) => s + l.debit, 0))}</td>
                                        <td>{formatNumber(selectedEntry.lines?.reduce((s, l) => s + l.credit, 0))}</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        <div className="modal-footer">
                            {selectedEntry.status === 'draft' && canPost && (
                                <button className="btn btn-success" onClick={() => handlePost(selectedEntry.id)}>
                                    ✓ {t('accounting.journal_entries.post_entry')}
                                </button>
                            )}
                            {selectedEntry.status === 'posted' && canVoid && (
                                <button className="btn btn-danger" onClick={() => handleVoid(selectedEntry.id)}>
                                    ✕ {t('accounting.journal_entries.void_entry')}
                                </button>
                            )}
                            <button className="btn btn-secondary" onClick={() => setSelectedEntry(null)}>
                                {t('accounting.journal_entries.close')}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default JournalEntryList
