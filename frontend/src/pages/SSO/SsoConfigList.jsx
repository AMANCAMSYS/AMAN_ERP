import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import api from '../../utils/api'
import { useToast } from '../../context/ToastContext'
import DataTable from '../../components/common/DataTable'
import SearchFilter from '../../components/common/SearchFilter'
import BackButton from '../../components/common/BackButton'

function SsoConfigList() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { showToast } = useToast()
    const [configs, setConfigs] = useState([])
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState('')
    const [statusFilter, setStatusFilter] = useState('')

    const fetchConfigs = async () => {
        try {
            setLoading(true)
            const res = await api.get('/auth/sso/config')
            setConfigs(res.data || [])
        } catch (err) {
            showToast(err.response?.data?.detail || t('common.error_loading'), 'error')
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { fetchConfigs() }, [])

    const handleDeactivate = async (id) => {
        try {
            await api.delete(`/auth/sso/config/${id}`)
            showToast(t('sso.deactivate') + ' ✓', 'success')
            fetchConfigs()
        } catch (err) {
            showToast(err.response?.data?.detail || t('common.error'), 'error')
        }
    }

    const filteredConfigs = useMemo(() => {
        let result = configs
        if (search) {
            const q = search.toLowerCase()
            result = result.filter(cfg =>
                (cfg.display_name || '').toLowerCase().includes(q) ||
                (cfg.ldap_host || '').toLowerCase().includes(q) ||
                (cfg.metadata_url || '').toLowerCase().includes(q)
            )
        }
        if (statusFilter) {
            result = result.filter(cfg =>
                statusFilter === 'active' ? cfg.is_active : !cfg.is_active
            )
        }
        return result
    }, [configs, search, statusFilter])

    const columns = [
        {
            key: 'provider_type',
            label: t('sso.provider_type'),
            render: (val) => (
                <span className={`badge badge-${val === 'saml' ? 'info' : 'warning'}`}>
                    {val?.toUpperCase()}
                </span>
            ),
        },
        {
            key: 'display_name',
            label: t('sso.display_name'),
            style: { fontWeight: 'bold' },
        },
        {
            key: 'ldap_host',
            label: t('sso.host_or_url'),
            render: (val, row) => val || row.metadata_url || '—',
        },
        {
            key: 'is_active',
            label: t('common.status.title', 'الحالة'),
            render: (val) => (
                <span className={`badge badge-${val ? 'success' : 'secondary'}`}>
                    {val ? t('common.active') : t('common.inactive')}
                </span>
            ),
        },
        {
            key: 'id',
            label: t('common.actions'),
            render: (val, row) => (
                <div style={{ display: 'flex', gap: 8 }}>
                    <button className="btn btn-sm btn-outline" onClick={(e) => { e.stopPropagation(); navigate(`/settings/sso/${val}`) }}>
                        {t('common.edit')}
                    </button>
                    {row.is_active && (
                        <button className="btn btn-sm btn-danger" onClick={(e) => { e.stopPropagation(); handleDeactivate(val) }}>
                            {t('sso.deactivate')}
                        </button>
                    )}
                </div>
            ),
        },
    ]

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className="workspace-title">{t('sso.config_title')}</h1>
                        <p className="workspace-subtitle">{t('sso.subtitle')}</p>
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                        <button className="btn btn-outline" onClick={() => navigate('/accounting/intercompany')}>
                            {t('sso.intercompany_button')}
                        </button>
                        <button className="btn btn-primary" onClick={() => navigate('/settings/sso/new')}>
                            + {t('sso.add_config')}
                        </button>
                    </div>
                </div>
            </div>

            <SearchFilter
                value={search}
                onChange={setSearch}
                placeholder={t('sso.search_placeholder')}
                filters={[{
                    key: 'status',
                    label: t('common.status.title', 'الحالة'),
                    options: [
                        { value: 'active', label: t('common.active') },
                        { value: 'inactive', label: t('common.inactive') },
                    ],
                }]}
                filterValues={{ status: statusFilter }}
                onFilterChange={(key, val) => setStatusFilter(val)}
            />

            <DataTable
                columns={columns}
                data={filteredConfigs}
                loading={loading}
                onRowClick={(row) => navigate(`/settings/sso/${row.id}`)}
                emptyTitle={t('sso.empty_title')}
                emptyDesc={t('sso.empty_desc')}
                emptyAction={{ label: t('sso.add_config'), onClick: () => navigate('/settings/sso/new') }}
            />
        </div>
    )
}

export default SsoConfigList
