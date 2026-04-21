import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { accountingAPI } from '../../utils/api'
import BackButton from '../../components/common/BackButton'
import FormField from '../../components/common/FormField'
import { useToast } from '../../context/ToastContext'
import { PageLoading } from '../../components/common/LoadingStates'

function EntityGroupTree() {
    const { t } = useTranslation()
    const { showToast } = useToast()
    const [entities, setEntities] = useState([])
    const [loading, setLoading] = useState(true)
    const [showForm, setShowForm] = useState(false)
    const [form, setForm] = useState({ name: '', parent_id: '', company_id: '', group_currency: 'SAR' })

    useEffect(() => { fetchEntities() }, [])

    const fetchEntities = async () => {
        try {
            setLoading(true)
            const res = await accountingAPI.listEntityGroups()
            setEntities(Array.isArray(res.data) ? res.data : [])
        } catch (e) {
            showToast(t('intercompany.load_error'), 'error')
        } finally {
            setLoading(false)
        }
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        try {
            await accountingAPI.createEntityGroup({
                ...form,
                parent_id: form.parent_id ? parseInt(form.parent_id) : null,
            })
            showToast(t('intercompany.entity_created'), 'success')
            setShowForm(false)
            setForm({ name: '', parent_id: '', company_id: '', group_currency: 'SAR' })
            fetchEntities()
        } catch (e) {
            showToast(e.response?.data?.detail || t('intercompany.create_error'), 'error')
        }
    }

    const buildTree = (items, parentId = null) => {
        return items
            .filter(i => (i.parent_id || null) === parentId)
            .map(item => ({
                ...item,
                children: buildTree(items, item.id),
            }))
    }

    const renderNode = (node, depth = 0) => (
        <div key={node.id} style={{ marginInlineStart: depth * 24 + 'px' }}>
            <div className="card" style={{ marginBottom: 8, padding: '12px 16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <strong>{node.name}</strong>
                        <span className="badge" style={{ marginInlineStart: 8, marginInlineEnd: 8 }}>
                            {t('intercompany.level')} {node.consolidation_level}
                        </span>
                        <small className="text-muted">{node.group_currency}</small>
                    </div>
                    <small className="text-muted">{node.company_id}</small>
                </div>
            </div>
            {node.children?.map(child => renderNode(child, depth + 1))}
        </div>
    )

    const tree = buildTree(entities)

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className="workspace-title">{t('intercompany.entity_tree_title')}</h1>
                        <p className="workspace-subtitle">{t('intercompany.entity_tree_subtitle')}</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
                        {showForm ? t('common.cancel') : t('intercompany.add_entity')}
                    </button>
                </div>
            </div>

            {showForm && (
                <form onSubmit={handleSubmit} className="card" style={{ padding: 16, marginBottom: 16 }}>
                    <div className="form-row">
                        <FormField label={t('intercompany.entity_name')} required>
                            <input type="text" className="form-input" required value={form.name}
                                onChange={e => setForm({ ...form, name: e.target.value })} />
                        </FormField>
                        <FormField label={t('intercompany.company_id')} required>
                            <input type="text" className="form-input" required value={form.company_id}
                                onChange={e => setForm({ ...form, company_id: e.target.value })} />
                        </FormField>
                        <FormField label={t('intercompany.group_currency')}>
                            <input type="text" className="form-input" value={form.group_currency}
                                onChange={e => setForm({ ...form, group_currency: e.target.value })} />
                        </FormField>
                        <FormField label={t('intercompany.parent_entity')}>
                            <select className="form-input" value={form.parent_id} onChange={e => setForm({ ...form, parent_id: e.target.value })}>
                                <option value="">{t('intercompany.root_entity')}</option>
                                {entities.map(ent => (
                                    <option key={ent.id} value={ent.id}>{ent.name}</option>
                                ))}
                            </select>
                        </FormField>
                    </div>
                    <button type="submit" className="btn btn-success">{t('common.save')}</button>
                </form>
            )}

            {loading ? (
                <PageLoading />
            ) : tree.length === 0 ? (
                <div className="card text-center py-5"><p className="text-muted">{t('intercompany.no_entities')}</p></div>
            ) : (
                <div className="ic-tree">{tree.map(node => renderNode(node))}</div>
            )}
        </div>
    )
}

export default EntityGroupTree
