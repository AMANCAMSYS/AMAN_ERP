import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import api from '../../utils/api'
import { useToast } from '../../context/ToastContext'
import BackButton from '../../components/common/BackButton'
import FormField from '../../components/common/FormField'
import DataTable from '../../components/common/DataTable'

function SsoConfigForm() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { showToast } = useToast()
    const { id } = useParams()
    const isEdit = id && id !== 'new'

    const [form, setForm] = useState({
        provider_type: 'ldap',
        display_name: '',
        metadata_url: '',
        metadata_xml: '',
        ldap_host: '',
        ldap_port: 636,
        ldap_base_dn: '',
        ldap_bind_dn: '',
        ldap_use_tls: true,
        is_active: false,
    })
    const [loading, setLoading] = useState(false)
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState('')
    const [ldapTestResult, setLdapTestResult] = useState(null)
    const [ldapTestPassword, setLdapTestPassword] = useState('')

    // Mappings state
    const [mappings, setMappings] = useState([])
    const [newMapping, setNewMapping] = useState({ external_group_name: '', aman_role_id: '' })
    const [roles, setRoles] = useState([])

    useEffect(() => {
        if (isEdit) {
            setLoading(true)
            api.get('/auth/sso/config').then(res => {
                const cfg = (res.data || []).find(c => c.id === Number(id))
                if (cfg) {
                    setForm({
                        provider_type: cfg.provider_type,
                        display_name: cfg.display_name || '',
                        metadata_url: cfg.metadata_url || '',
                        metadata_xml: '',
                        ldap_host: cfg.ldap_host || '',
                        ldap_port: cfg.ldap_port || 636,
                        ldap_base_dn: cfg.ldap_base_dn || '',
                        ldap_bind_dn: cfg.ldap_bind_dn || '',
                        ldap_use_tls: cfg.ldap_use_tls ?? true,
                        is_active: cfg.is_active ?? false,
                    })
                }
            }).catch(() => {}).finally(() => setLoading(false))

            // Load mappings
            api.get('/auth/sso/mappings', { params: { sso_configuration_id: Number(id) } })
                .then(res => setMappings(res.data || []))
                .catch(() => {})
        }

        // Load roles for mapping dropdown
        api.get('/roles').then(res => setRoles(res.data || [])).catch(() => {})
    }, [id, isEdit])

    const handleChange = (field, value) => setForm(prev => ({ ...prev, [field]: value }))

    const handleSubmit = async (e) => {
        e.preventDefault()
        setSaving(true)
        setError('')
        try {
            if (isEdit) {
                await api.put(`/auth/sso/config/${id}`, form)
            } else {
                await api.post('/auth/sso/config', form)
            }
            navigate('/settings/sso')
        } catch (err) {
            setError(err.response?.data?.detail || t('common.error'))
        } finally {
            setSaving(false)
        }
    }

    const handleLdapTest = async () => {
        setLdapTestResult(null)
        try {
            const res = await api.post('/auth/sso/ldap/test', {
                ldap_host: form.ldap_host,
                ldap_port: form.ldap_port,
                ldap_base_dn: form.ldap_base_dn,
                ldap_bind_dn: form.ldap_bind_dn,
                ldap_bind_password: ldapTestPassword,
                ldap_use_tls: form.ldap_use_tls,
            })
            setLdapTestResult(res.data)
        } catch (err) {
            setLdapTestResult({ success: false, message: err.response?.data?.detail || t('common.error') })
        }
    }

    const handleAddMapping = async () => {
        if (!newMapping.external_group_name || !newMapping.aman_role_id) return
        try {
            const res = await api.post('/auth/sso/mappings', {
                sso_configuration_id: Number(id),
                external_group_name: newMapping.external_group_name,
                aman_role_id: Number(newMapping.aman_role_id),
            })
            setMappings(prev => [...prev, res.data])
            setNewMapping({ external_group_name: '', aman_role_id: '' })
        } catch (err) {
            showToast(err.response?.data?.detail || t('common.error'), 'error')
        }
    }

    if (loading) return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <h1 className="workspace-title">{t('sso.loading')}</h1>
            </div>
            <div className="loading-container"><span className="loading"></span></div>
        </div>
    )

    const mappingColumns = [
        { key: 'external_group_name', label: t('sso.external_group') },
        {
            key: 'aman_role_id',
            label: t('sso.aman_role'),
            render: (val) => roles.find(r => r.id === val)?.role_name || val,
        },
    ]

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <h1 className="workspace-title">
                    {isEdit ? t('sso.edit_config') : t('sso.new_config')}
                </h1>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <form onSubmit={handleSubmit}>
                <div className="card">
                    <FormField label={t('sso.provider_type')}>
                        <select className="form-input" value={form.provider_type} onChange={e => handleChange('provider_type', e.target.value)} disabled={isEdit}>
                            <option value="ldap">LDAP</option>
                            <option value="saml">SAML</option>
                        </select>
                    </FormField>

                    <FormField label={t('sso.display_name')} required>
                        <input className="form-input" value={form.display_name} onChange={e => handleChange('display_name', e.target.value)} required />
                    </FormField>

                    <FormField>
                        <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                            <input type="checkbox" checked={form.is_active} onChange={e => handleChange('is_active', e.target.checked)} />
                            {t('sso.is_active')}
                        </label>
                    </FormField>

                    {form.provider_type === 'saml' && (
                        <>
                            <FormField label={t('sso.metadata_url')}>
                                <input className="form-input" value={form.metadata_url} onChange={e => handleChange('metadata_url', e.target.value)} placeholder="https://idp.example.com/metadata" />
                            </FormField>
                            <FormField label={t('sso.metadata_xml')}>
                                <textarea className="form-input" rows={4} value={form.metadata_xml} onChange={e => handleChange('metadata_xml', e.target.value)} />
                            </FormField>
                        </>
                    )}

                    {form.provider_type === 'ldap' && (
                        <>
                            <div className="form-row">
                                <FormField label={t('sso.ldap_host')} required style={{ flex: 2 }}>
                                    <input className="form-input" value={form.ldap_host} onChange={e => handleChange('ldap_host', e.target.value)} placeholder="ldap.corp.example.com" />
                                </FormField>
                                <FormField label={t('sso.ldap_port')} style={{ flex: 1 }}>
                                    <input className="form-input" type="number" value={form.ldap_port} onChange={e => handleChange('ldap_port', Number(e.target.value))} />
                                </FormField>
                            </div>
                            <FormField label={t('sso.ldap_base_dn')} required>
                                <input className="form-input" value={form.ldap_base_dn} onChange={e => handleChange('ldap_base_dn', e.target.value)} placeholder="dc=corp,dc=example,dc=com" />
                            </FormField>
                            <FormField label={t('sso.ldap_bind_dn')}>
                                <input className="form-input" value={form.ldap_bind_dn} onChange={e => handleChange('ldap_bind_dn', e.target.value)} placeholder="cn=admin,dc=corp,dc=example,dc=com" />
                            </FormField>
                            <FormField>
                                <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                                    <input type="checkbox" checked={form.ldap_use_tls} onChange={e => handleChange('ldap_use_tls', e.target.checked)} />
                                    {t('sso.use_tls')}
                                </label>
                            </FormField>

                            {/* LDAP Test */}
                            <div style={{ background: 'var(--bg-secondary)', padding: 16, borderRadius: 8, marginTop: 12 }}>
                                <FormField label={t('sso.test_connection')}>
                                    <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                                        <input className="form-input" type="password" value={ldapTestPassword} onChange={e => setLdapTestPassword(e.target.value)} placeholder={t('sso.bind_password')} style={{ flex: 1 }} />
                                        <button type="button" className="btn btn-outline" onClick={handleLdapTest}>{t('sso.test_btn')}</button>
                                    </div>
                                    {ldapTestResult && (
                                        <div className={`alert ${ldapTestResult.success ? 'alert-success' : 'alert-error'}`} style={{ marginTop: 8 }}>
                                            {ldapTestResult.message}
                                        </div>
                                    )}
                                </FormField>
                            </div>
                        </>
                    )}
                </div>

                <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
                    <button type="submit" className="btn btn-primary" disabled={saving}>
                        {saving ? <span className="loading"></span> : t('common.save')}
                    </button>
                    <button type="button" className="btn btn-outline" onClick={() => navigate('/settings/sso')}>
                        {t('common.cancel')}
                    </button>
                </div>
            </form>

            {/* Group-Role Mappings (only in edit mode) */}
            {isEdit && (
                <div className="card" style={{ marginTop: 24 }}>
                    <h3>{t('sso.group_role_mappings')}</h3>

                    <DataTable
                        columns={mappingColumns}
                        data={mappings}
                        paginate={false}
                    />

                    <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                        <input className="form-input" value={newMapping.external_group_name} onChange={e => setNewMapping(p => ({ ...p, external_group_name: e.target.value }))} placeholder={t('sso.group_name_placeholder')} style={{ flex: 1 }} />
                        <select className="form-input" value={newMapping.aman_role_id} onChange={e => setNewMapping(p => ({ ...p, aman_role_id: e.target.value }))} style={{ flex: 1 }}>
                            <option value="">{t('sso.select_role')}</option>
                            {roles.map(r => <option key={r.id} value={r.id}>{r.role_name}</option>)}
                        </select>
                        <button type="button" className="btn btn-primary btn-sm" onClick={handleAddMapping}>{t('common.add')}</button>
                    </div>
                </div>
            )}
        </div>
    )
}

export default SsoConfigForm
