import { useState, useEffect } from 'react'
import { printTemplatesAPI } from '../../utils/api'
import { useTranslation } from 'react-i18next'
import { useToast } from '../../context/ToastContext'
import BackButton from '../../components/common/BackButton'
import { PageLoading } from '../../components/common/LoadingStates'

function PrintTemplates() {
    const { t } = useTranslation()
    const { showToast } = useToast()
    const [templates, setTemplates] = useState([])
    const [loading, setLoading] = useState(true)
    const [showForm, setShowForm] = useState(false)
    const [editId, setEditId] = useState(null)
    const [form, setForm] = useState({
        name: '', document_type: 'invoice', template_html: '', is_default: false,
        header_html: '', footer_html: '', page_size: 'A4'
    })

    const fetchTemplates = async () => {
        try { const r = await printTemplatesAPI.list(); setTemplates(r.data) }
        catch { console.error }
        finally { setLoading(false) }
    }

    useEffect(() => { fetchTemplates() }, [])

    const handleEdit = async (id) => {
        try {
            const r = await printTemplatesAPI.get(id)
            setForm(r.data)
            setEditId(id)
            setShowForm(true)
        } catch { showToast(t('common.error'), 'error') }
    }

    const handleSave = async () => {
        try {
            if (editId) {
                await printTemplatesAPI.update(editId, form)
            } else {
                await printTemplatesAPI.create(form)
            }
            showToast(t('common.saved'), 'success')
            setShowForm(false)
            setEditId(null)
            setForm({ name: '', document_type: 'invoice', template_html: '', is_default: false, header_html: '', footer_html: '', page_size: 'A4' })
            fetchTemplates()
        } catch (err) {
            showToast(err.response?.data?.detail || t('common.error'), 'error')
        }
    }

    if (loading) return <PageLoading />

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">🖨️ {t('print_templates.title')}</h1>
                    <p className="workspace-subtitle">{t('print_templates.subtitle')}</p>
                </div>
                <div className="header-actions">
                    <button className="btn btn-primary" onClick={() => { setShowForm(!showForm); setEditId(null) }}>
                        + {t('print_templates.create_new')}
                    </button>
                </div>
            </div>

            {showForm && (
                <div className="card p-4 mb-4">
                    <h3 className="card-title mb-3">{editId ? t('print_templates.edit') : t('print_templates.create_new')}</h3>
                    <div className="form-grid-3">
                        <div className="form-group">
                            <label>{t('common.name')} *</label>
                            <input type="text" className="form-input" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
                        </div>
                        <div className="form-group">
                            <label>{t('print_templates.document_type')}</label>
                            <select className="form-select" value={form.document_type} onChange={e => setForm(f => ({ ...f, document_type: e.target.value }))}>
                                <option value="invoice">{t('print_templates.type_invoice')}</option>
                                <option value="quotation">{t('print_templates.type_quotation')}</option>
                                <option value="purchase_order">{t('print_templates.type_po')}</option>
                                <option value="delivery_order">{t('print_templates.type_do')}</option>
                                <option value="receipt">{t('print_templates.type_receipt')}</option>
                                <option value="payslip">{t('print_templates.type_payslip')}</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label>{t('print_templates.page_size')}</label>
                            <select className="form-select" value={form.page_size} onChange={e => setForm(f => ({ ...f, page_size: e.target.value }))}>
                                <option value="A4">A4</option>
                                <option value="A5">A5</option>
                                <option value="Letter">Letter</option>
                            </select>
                        </div>
                    </div>

                    <div className="form-group mt-3">
                        <label>{t('print_templates.header_html')}</label>
                        <textarea className="form-input" rows="3" value={form.header_html} onChange={e => setForm(f => ({ ...f, header_html: e.target.value }))} placeholder="<div>Company Logo & Info</div>" />
                    </div>
                    <div className="form-group mt-3">
                        <label>{t('print_templates.template_html')} *</label>
                        <textarea className="form-input" rows="8" value={form.template_html} onChange={e => setForm(f => ({ ...f, template_html: e.target.value }))} placeholder="<table>{{#lines}}<tr><td>{{product_name}}</td></tr>{{/lines}}</table>" />
                    </div>
                    <div className="form-group mt-3">
                        <label>{t('print_templates.footer_html')}</label>
                        <textarea className="form-input" rows="3" value={form.footer_html} onChange={e => setForm(f => ({ ...f, footer_html: e.target.value }))} placeholder="<div>Terms & Conditions</div>" />
                    </div>

                    <div className="mt-2">
                        <label className="flex items-center gap-2">
                            <input type="checkbox" checked={form.is_default} onChange={e => setForm(f => ({ ...f, is_default: e.target.checked }))} />
                            {t('print_templates.set_default')}
                        </label>
                    </div>

                    <div className="mt-3 flex gap-2">
                        <button className="btn btn-primary" onClick={handleSave}>{t('common.save')}</button>
                        <button className="btn btn-secondary" onClick={() => { setShowForm(false); setEditId(null) }}>{t('common.cancel')}</button>
                    </div>
                </div>
            )}

            <div className="card">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>{t('common.name')}</th>
                            <th>{t('print_templates.document_type')}</th>
                            <th>{t('print_templates.page_size')}</th>
                            <th>{t('print_templates.default')}</th>
                            <th>{t('common.actions')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {templates.length === 0 ? (
                            <tr><td colSpan="5" className="text-center py-5 text-muted">{t('print_templates.empty')}</td></tr>
                        ) : templates.map(tmpl => (
                            <tr key={tmpl.id}>
                                <td className="font-medium">{tmpl.name}</td>
                                <td>{t(`print_templates.type_${tmpl.document_type}`, tmpl.document_type)}</td>
                                <td>{tmpl.page_size || 'A4'}</td>
                                <td>{tmpl.is_default ? '⭐' : '-'}</td>
                                <td>
                                    <button className="btn btn-secondary btn-sm" onClick={() => handleEdit(tmpl.id)}>
                                        ✏️ {t('common.edit')}
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}

export default PrintTemplates
