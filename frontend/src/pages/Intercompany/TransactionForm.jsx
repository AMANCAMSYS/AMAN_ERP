import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { accountingAPI } from '../../utils/api'
import BackButton from '../../components/common/BackButton'
import FormField from '../../components/common/FormField'
import { useToast } from '../../context/ToastContext'

function TransactionForm() {
    const { t } = useTranslation()
    const { showToast } = useToast()
    const navigate = useNavigate()
    const [entities, setEntities] = useState([])
    const [loading, setLoading] = useState(false)
    const [form, setForm] = useState({
        source_entity_id: '',
        target_entity_id: '',
        transaction_type: 'sale',
        source_amount: '',
        source_currency: 'SAR',
        target_currency: 'SAR',
        exchange_rate: '1',
        reference_document: '',
    })

    useEffect(() => {
        accountingAPI.listEntityGroups()
            .then(res => setEntities(Array.isArray(res.data) ? res.data : []))
            .catch(() => {})
    }, [])

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (form.source_entity_id === form.target_entity_id) {
            showToast(t('intercompany.same_entity_error'), 'error')
            return
        }
        try {
            setLoading(true)
            await accountingAPI.createICTransactionV2({
                ...form,
                source_entity_id: parseInt(form.source_entity_id),
                target_entity_id: parseInt(form.target_entity_id),
                source_amount: parseFloat(form.source_amount),
                exchange_rate: parseFloat(form.exchange_rate),
            })
            showToast(t('intercompany.transaction_created'), 'success')
            navigate('/accounting/intercompany/transactions')
        } catch (e) {
            showToast(e.response?.data?.detail || t('intercompany.create_error'), 'error')
        } finally {
            setLoading(false)
        }
    }

    const updateField = (field, value) => setForm(prev => ({ ...prev, [field]: value }))

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <h1 className="workspace-title">{t('intercompany.new_transaction')}</h1>
            </div>

            <form onSubmit={handleSubmit} className="card" style={{ padding: 16 }}>
                <div className="form-row">
                    <FormField label={t('intercompany.source_entity')} required>
                        <select className="form-input" required value={form.source_entity_id}
                            onChange={e => updateField('source_entity_id', e.target.value)}>
                            <option value="">{t('common.select')}</option>
                            {entities.map(ent => <option key={ent.id} value={ent.id}>{ent.name}</option>)}
                        </select>
                    </FormField>
                    <FormField label={t('intercompany.target_entity')} required>
                        <select className="form-input" required value={form.target_entity_id}
                            onChange={e => updateField('target_entity_id', e.target.value)}>
                            <option value="">{t('common.select')}</option>
                            {entities.map(ent => <option key={ent.id} value={ent.id}>{ent.name}</option>)}
                        </select>
                    </FormField>
                </div>

                <div className="form-row">
                    <FormField label={t('intercompany.type')}>
                        <select className="form-input" value={form.transaction_type} onChange={e => updateField('transaction_type', e.target.value)}>
                            <option value="sale">{t('intercompany.type_sale')}</option>
                            <option value="purchase">{t('intercompany.type_purchase')}</option>
                            <option value="service">{t('intercompany.type_service')}</option>
                            <option value="loan">{t('intercompany.type_loan')}</option>
                            <option value="transfer">{t('intercompany.type_transfer')}</option>
                        </select>
                    </FormField>
                    <FormField label={t('intercompany.source_amount')} required>
                        <input className="form-input" type="number" step="0.0001" required value={form.source_amount}
                            onChange={e => updateField('source_amount', e.target.value)} />
                    </FormField>
                </div>

                <div className="form-row">
                    <FormField label={t('intercompany.source_currency')}>
                        <input className="form-input" type="text" value={form.source_currency}
                            onChange={e => updateField('source_currency', e.target.value)} />
                    </FormField>
                    <FormField label={t('intercompany.target_currency')}>
                        <input className="form-input" type="text" value={form.target_currency}
                            onChange={e => updateField('target_currency', e.target.value)} />
                    </FormField>
                    <FormField label={t('intercompany.exchange_rate')}>
                        <input className="form-input" type="number" step="0.00000001" value={form.exchange_rate}
                            onChange={e => updateField('exchange_rate', e.target.value)} />
                    </FormField>
                </div>

                <div className="form-row">
                    <FormField label={t('intercompany.reference')} style={{ flex: 1 }}>
                        <input className="form-input" type="text" value={form.reference_document}
                            onChange={e => updateField('reference_document', e.target.value)} />
                    </FormField>
                </div>

                <div style={{ marginTop: 16 }}>
                    <button type="submit" className="btn btn-success" disabled={loading}>
                        {loading ? t('common.saving') : t('intercompany.create_transaction')}
                    </button>
                    <button type="button" className="btn btn-secondary" style={{ marginInlineEnd: 8 }}
                        onClick={() => navigate('/accounting/intercompany/transactions')}>
                        {t('common.cancel')}
                    </button>
                </div>
            </form>
        </div>
    )
}

export default TransactionForm
