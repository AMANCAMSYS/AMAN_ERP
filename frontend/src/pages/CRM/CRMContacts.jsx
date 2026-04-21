import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { crmAPI, partiesAPI } from '../../utils/api'
import BackButton from '../../components/common/BackButton'
import '../../components/ModuleStyles.css'
import { useToast } from '../../context/ToastContext'
import { PageLoading } from '../../components/common/LoadingStates'

function CRMContacts() {
    const { t } = useTranslation()
  const { showToast } = useToast()
    const [contacts, setContacts] = useState([])
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState('')
    const [showForm, setShowForm] = useState(false)
    const [editingId, setEditingId] = useState(null)
    const [customers, setCustomers] = useState([])   // T021: customer list for dropdown
    const [customerSearch, setCustomerSearch] = useState('')  // T021: filter text
    const [form, setForm] = useState({
        customer_id: '', first_name: '', last_name: '', job_title: '',
        email: '', phone: '', mobile: '', department: '',
        is_primary: false, is_decision_maker: false, notes: ''
    })

    useEffect(() => { fetchContacts(); fetchCustomers() }, [])

    const fetchContacts = async () => {
        try {
            setLoading(true)
            const res = await crmAPI.listContacts()
            setContacts(res.data)
        } catch (err) {
            console.error('Failed to fetch contacts', err)
        } finally {
            setLoading(false)
        }
    }

    // T021: fetch customer list for the dropdown
    const fetchCustomers = async () => {
        try {
            const res = await partiesAPI.getCustomers({ limit: 200 })
            setCustomers(res.data?.items || res.data || [])
        } catch (err) {
            console.error('Failed to fetch customers', err)
        }
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        try {
            const payload = {
                ...form,
                customer_id: parseInt(form.customer_id)
            }
            if (editingId) {
                await crmAPI.updateContact(editingId, payload)
            } else {
                await crmAPI.createContact(payload)
            }
            resetForm()
            fetchContacts()
        } catch (err) {
            showToast(err.response?.data?.detail || 'Error', 'error')
        }
    }

    const resetForm = () => {
        setShowForm(false)
        setEditingId(null)
        setCustomerSearch('')
        setForm({
            customer_id: '', first_name: '', last_name: '', job_title: '',
            email: '', phone: '', mobile: '', department: '',
            is_primary: false, is_decision_maker: false, notes: ''
        })
    }

    const handleEdit = (c) => {
        setEditingId(c.id)
        setForm({
            customer_id: c.customer_id || '', first_name: c.first_name || '', last_name: c.last_name || '',
            job_title: c.job_title || '', email: c.email || '', phone: c.phone || '',
            mobile: c.mobile || '', department: c.department || '',
            is_primary: c.is_primary || false, is_decision_maker: c.is_decision_maker || false,
            notes: c.notes || ''
        })
        setShowForm(true)
    }

    const filtered = contacts.filter(c => {
        if (!search) return true
        const q = search.toLowerCase()
        return (c.first_name || '').toLowerCase().includes(q) ||
            (c.last_name || '').toLowerCase().includes(q) ||
            (c.email || '').toLowerCase().includes(q) ||
            (c.customer_name || '').toLowerCase().includes(q) ||
            (c.job_title || '').toLowerCase().includes(q)
    })

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div>
                    <h1 className="workspace-title">{t('crm.contacts', 'جهات الاتصال')}</h1>
                    <p className="workspace-subtitle">{t('crm.contacts_desc', 'إدارة جهات اتصال العملاء والشركات')}</p>
                </div>
            </div>

            {/* Actions Bar */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, gap: 12, flexWrap: 'wrap' }}>
                <input
                    className="form-input"
                    placeholder={t('common.search', 'بحث...')}
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    style={{ maxWidth: 300 }}
                />
                <button className="btn btn-primary btn-sm" onClick={() => { showForm ? resetForm() : setShowForm(true) }}>
                    {showForm ? t('common.cancel', 'إلغاء') : t('crm.add_contact', '+ جهة اتصال')}
                </button>
            </div>

            {/* Create / Edit Form */}
            {showForm && (
                <div className="section-card" style={{ marginBottom: 16 }}>
                    <h3 className="section-title">
                        {editingId ? t('crm.edit_contact', 'تعديل جهة الاتصال') : t('crm.new_contact', 'جهة اتصال جديدة')}
                    </h3>
                    <form onSubmit={handleSubmit}>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
                            <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                                <label className="form-label">{t('common.customer', 'العميل')} *</label>
                                <input
                                    className="form-input"
                                    placeholder={t('common.search', 'بحث باسم العميل...')}
                                    value={customerSearch}
                                    onChange={e => setCustomerSearch(e.target.value)}
                                    style={{ marginBottom: 4 }}
                                />
                                {customers.length === 0 ? (
                                    <p style={{ fontSize: 12, color: '#9ca3af', margin: '4px 0 0' }}>
                                        {t('common.loading', 'جارٍ التحميل...')}
                                    </p>
                                ) : (
                                    <select
                                        className="form-input"
                                        required
                                        value={form.customer_id}
                                        onChange={e => setForm({ ...form, customer_id: e.target.value })}
                                    >
                                        <option value="">{t('common.select_customer', '-- اختر العميل --')}</option>
                                        {customers
                                            .filter(c => !customerSearch ||
                                                (c.name || '').toLowerCase().includes(customerSearch.toLowerCase()))
                                            .map(c => (
                                                <option key={c.id} value={c.id}>{c.name}</option>
                                            ))}
                                    </select>
                                )}
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('crm.first_name', 'الاسم الأول')} *</label>
                                <input className="form-input" required value={form.first_name}
                                    onChange={e => setForm({ ...form, first_name: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('crm.last_name', 'اسم العائلة')}</label>
                                <input className="form-input" value={form.last_name}
                                    onChange={e => setForm({ ...form, last_name: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('crm.job_title', 'المسمى الوظيفي')}</label>
                                <input className="form-input" value={form.job_title}
                                    onChange={e => setForm({ ...form, job_title: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('common.email', 'البريد الإلكتروني')}</label>
                                <input className="form-input" type="email" value={form.email}
                                    onChange={e => setForm({ ...form, email: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('common.phone', 'الهاتف')}</label>
                                <input className="form-input" value={form.phone} dir="ltr"
                                    onChange={e => setForm({ ...form, phone: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('crm.mobile', 'الجوال')}</label>
                                <input className="form-input" value={form.mobile} dir="ltr"
                                    onChange={e => setForm({ ...form, mobile: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('crm.department', 'القسم')}</label>
                                <input className="form-input" value={form.department}
                                    onChange={e => setForm({ ...form, department: e.target.value })} />
                            </div>
                        </div>
                        <div style={{ display: 'flex', gap: 16, marginTop: 12 }}>
                            <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                                <input type="checkbox" checked={form.is_primary}
                                    onChange={e => setForm({ ...form, is_primary: e.target.checked })} />
                                {t('crm.is_primary', 'جهة اتصال أساسية')}
                            </label>
                            <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                                <input type="checkbox" checked={form.is_decision_maker}
                                    onChange={e => setForm({ ...form, is_decision_maker: e.target.checked })} />
                                {t('crm.is_decision_maker', 'صانع قرار')}
                            </label>
                        </div>
                        <div className="form-group" style={{ marginTop: 12 }}>
                            <label className="form-label">{t('common.notes', 'ملاحظات')}</label>
                            <textarea className="form-input" rows={2} value={form.notes}
                                onChange={e => setForm({ ...form, notes: e.target.value })} />
                        </div>
                        <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
                            <button type="submit" className="btn btn-primary btn-sm">{t('common.save', 'حفظ')}</button>
                            <button type="button" className="btn btn-secondary btn-sm" onClick={resetForm}>{t('common.cancel', 'إلغاء')}</button>
                        </div>
                    </form>
                </div>
            )}

            {loading ? (
                <PageLoading />
            ) : (
                <div className="section-card">
                    <h3 className="section-title">{t('crm.contacts_list', 'قائمة جهات الاتصال')} ({filtered.length})</h3>
                    {filtered.length === 0 ? (
                        <p style={{ color: '#9ca3af', textAlign: 'center', padding: 24 }}>
                            {t('crm.no_contacts', 'لا توجد جهات اتصال')}
                        </p>
                    ) : (
                        <div className="data-table-container">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>{t('common.name', 'الاسم')}</th>
                                        <th>{t('common.customer', 'العميل')}</th>
                                        <th>{t('crm.job_title', 'المسمى')}</th>
                                        <th>{t('common.email', 'البريد')}</th>
                                        <th>{t('common.phone', 'الهاتف')}</th>
                                        <th>{t('crm.role', 'الدور')}</th>
                                        <th>{t('common.actions', 'إجراءات')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filtered.map(c => (
                                        <tr key={c.id}>
                                            <td style={{ fontWeight: 600 }}>
                                                {c.first_name} {c.last_name || ''}
                                            </td>
                                            <td>{c.customer_name || `#${c.customer_id}`}</td>
                                            <td>{c.job_title || '—'}</td>
                                            <td>
                                                {c.email ? (
                                                    <a href={`mailto:${c.email}`} style={{ color: '#3b82f6' }}>{c.email}</a>
                                                ) : '—'}
                                            </td>
                                            <td dir="ltr">{c.phone || c.mobile || '—'}</td>
                                            <td>
                                                <div style={{ display: 'flex', gap: 4 }}>
                                                    {c.is_primary && <span className="badge badge-primary">{t('crm.primary', 'أساسي')}</span>}
                                                    {c.is_decision_maker && <span className="badge badge-warning">{t('crm.decision_maker', 'قرار')}</span>}
                                                </div>
                                            </td>
                                            <td>
                                                <button className="btn btn-info btn-sm" style={{ padding: '3px 8px', fontSize: '0.75rem' }}
                                                    onClick={() => handleEdit(c)}>
                                                    {t('common.edit', 'تعديل')}
                                                </button>
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

export default CRMContacts
