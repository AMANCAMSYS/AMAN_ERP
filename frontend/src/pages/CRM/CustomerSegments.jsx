import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { crmAPI } from '../../utils/api'
import BackButton from '../../components/common/BackButton'
import '../../components/ModuleStyles.css'
import { useToast } from '../../context/ToastContext'
import { PageLoading } from '../../components/common/LoadingStates'

function CustomerSegments() {
    const { t } = useTranslation()
  const { showToast } = useToast()
    const [segments, setSegments] = useState([])
    const [loading, setLoading] = useState(true)
    const [showForm, setShowForm] = useState(false)
    const [selectedSegment, setSelectedSegment] = useState(null)
    const [members, setMembers] = useState([])
    const [membersLoading, setMembersLoading] = useState(false)
    const [form, setForm] = useState({ name: '', description: '', color: '#3B82F6', auto_assign: false })

    useEffect(() => { fetchSegments() }, [])

    const fetchSegments = async () => {
        try {
            setLoading(true)
            const res = await crmAPI.listSegments()
            setSegments(res.data)
        } catch (err) {
            console.error('Failed to fetch segments', err)
        } finally {
            setLoading(false)
        }
    }

    const handleCreate = async (e) => {
        e.preventDefault()
        try {
            await crmAPI.createSegment({
                name: form.name,
                description: form.description,
                color: form.color,
                auto_assign: form.auto_assign
            })
            setShowForm(false)
            setForm({ name: '', description: '', color: '#3B82F6', auto_assign: false })
            fetchSegments()
        } catch (err) {
            showToast(err.response?.data?.detail || 'Error', 'error')
        }
    }

    const handleDelete = async (id) => {
        if (!confirm(t('common.confirm_delete', 'هل أنت متأكد من الحذف؟'))) return
        try {
            await crmAPI.deleteSegment(id)
            if (selectedSegment?.id === id) {
                setSelectedSegment(null)
                setMembers([])
            }
            fetchSegments()
        } catch (err) {
            showToast(err.response?.data?.detail || 'Error', 'error')
        }
    }

    const viewMembers = async (seg) => {
        setSelectedSegment(seg)
        setMembersLoading(true)
        try {
            const res = await crmAPI.getSegmentMembers(seg.id)
            setMembers(res.data)
        } catch (err) {
            console.error('Failed to fetch segment members', err)
            setMembers([])
        } finally {
            setMembersLoading(false)
        }
    }

    const COLORS = ['#3B82F6', '#22C55E', '#F97316', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6', '#F59E0B']

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div>
                    <h1 className="workspace-title">{t('crm.customer_segments', 'شرائح العملاء')}</h1>
                    <p className="workspace-subtitle">{t('crm.segments_desc', 'تصنيف العملاء إلى شرائح لاستهداف أفضل')}</p>
                </div>
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
                <button className="btn btn-primary btn-sm" onClick={() => setShowForm(!showForm)}>
                    {showForm ? t('common.cancel', 'إلغاء') : t('crm.add_segment', '+ شريحة جديدة')}
                </button>
            </div>

            {/* Create Form */}
            {showForm && (
                <div className="modal-overlay" onClick={() => setShowForm(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 760, width: '92%' }}>
                        <div className="modal-header">
                            <h2 className="modal-title">{t('crm.new_segment', 'شريحة جديدة')}</h2>
                            <button type="button" className="btn-icon" onClick={() => setShowForm(false)}>✕</button>
                        </div>
                        <form onSubmit={handleCreate}>
                            <div className="modal-body">
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
                                    <div className="form-group">
                                        <label className="form-label">{t('common.name', 'الاسم')}</label>
                                        <input className="form-input" required value={form.name}
                                            onChange={e => setForm({ ...form, name: e.target.value })} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">{t('common.description', 'الوصف')}</label>
                                        <input className="form-input" value={form.description}
                                            onChange={e => setForm({ ...form, description: e.target.value })} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">{t('crm.color', 'اللون')}</label>
                                        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                                            {COLORS.map(c => (
                                                <div key={c} onClick={() => setForm({ ...form, color: c })}
                                                    style={{
                                                        width: 28, height: 28, borderRadius: '50%', backgroundColor: c,
                                                        cursor: 'pointer', border: form.color === c ? '3px solid #1f2937' : '2px solid transparent',
                                                        transition: '0.15s'
                                                    }} />
                                            ))}
                                        </div>
                                    </div>
                                    <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: 8, paddingTop: 24 }}>
                                        <input type="checkbox" id="auto_assign" checked={form.auto_assign}
                                            onChange={e => setForm({ ...form, auto_assign: e.target.checked })} />
                                        <label htmlFor="auto_assign" className="form-label" style={{ margin: 0 }}>
                                            {t('crm.auto_assign', 'تعيين تلقائي')}
                                        </label>
                                    </div>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)}>{t('common.cancel', 'إلغاء')}</button>
                                <button type="submit" className="btn btn-primary">{t('common.save', 'حفظ')}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {loading ? (
                <PageLoading />
            ) : segments.length === 0 ? (
                <div className="section-card" style={{ textAlign: 'center', padding: 40, color: '#9ca3af' }}>
                    {t('crm.no_segments', 'لا توجد شرائح بعد')}
                </div>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
                    {segments.map(seg => (
                        <div key={seg.id} className="section-card" style={{
                            borderTop: `4px solid ${seg.color || '#3B82F6'}`,
                            cursor: 'pointer',
                            transition: '0.2s',
                            position: 'relative'
                        }} onClick={() => viewMembers(seg)}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <div>
                                    <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#1f2937', marginBottom: 4 }}>
                                        {seg.name}
                                    </h3>
                                    {seg.description && (
                                        <p style={{ fontSize: '0.85rem', color: '#6b7280', marginBottom: 8 }}>
                                            {seg.description}
                                        </p>
                                    )}
                                </div>
                                <button className="btn btn-danger btn-sm" style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                                    onClick={(e) => { e.stopPropagation(); handleDelete(seg.id) }}>
                                    ✕
                                </button>
                            </div>
                            <div style={{ display: 'flex', gap: 16, marginTop: 8 }}>
                                <div>
                                    <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>{t('crm.members', 'الأعضاء')}</div>
                                    <div style={{ fontSize: '1.25rem', fontWeight: 700, color: seg.color || '#3B82F6' }}>
                                        {seg.member_count || 0}
                                    </div>
                                </div>
                                {seg.auto_assign && (
                                    <span className="badge badge-info" style={{ alignSelf: 'flex-end' }}>
                                        {t('crm.auto', 'تلقائي')}
                                    </span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Members Panel */}
            {selectedSegment && (
                <div className="section-card" style={{ marginTop: 20 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                        <h3 className="section-title" style={{ marginBottom: 0 }}>
                            {t('crm.segment_members', 'أعضاء شريحة')}: {selectedSegment.name}
                        </h3>
                        <button className="btn btn-secondary btn-sm" onClick={() => { setSelectedSegment(null); setMembers([]) }}>
                            {t('common.close', 'إغلاق')}
                        </button>
                    </div>
                    {membersLoading ? (
                        <PageLoading />
                    ) : members.length === 0 ? (
                        <p style={{ color: '#9ca3af', textAlign: 'center', padding: 16 }}>
                            {t('crm.no_members', 'لا يوجد أعضاء في هذه الشريحة')}
                        </p>
                    ) : (
                        <div className="data-table-container">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>{t('common.name', 'الاسم')}</th>
                                        <th>{t('common.email', 'البريد')}</th>
                                        <th>{t('common.phone', 'الهاتف')}</th>
                                        <th>{t('common.type', 'النوع')}</th>
                                        <th>{t('crm.added_at', 'تاريخ الإضافة')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {members.map(m => (
                                        <tr key={m.id}>
                                            <td style={{ fontWeight: 600 }}>{m.name}</td>
                                            <td>{m.email || '—'}</td>
                                            <td dir="ltr">{m.phone || '—'}</td>
                                            <td><span className="badge badge-info">{m.party_type}</span></td>
                                            <td style={{ color: '#9ca3af', fontSize: '0.85rem' }}>
                                                {m.added_at ? new Date(m.added_at).toLocaleDateString('ar-SA') : '—'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

export default CustomerSegments
