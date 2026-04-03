import { useState, useEffect } from 'react'
import { purchasesAPI } from '../../utils/api'
import { useTranslation } from 'react-i18next'
import { useToast } from '../../context/ToastContext'
import BackButton from '../../components/common/BackButton'
import FormField from '../../components/common/FormField'
import DataTable from '../../components/common/DataTable'

export default function ToleranceConfig() {
  const { t } = useTranslation()
  const { showToast } = useToast()
  const [tolerances, setTolerances] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [editing, setEditing] = useState(null) // null = list, object = form

  useEffect(() => { loadTolerances() }, [])

  const loadTolerances = async () => {
    try {
      setLoading(true)
      const res = await purchasesAPI.listTolerances()
      setTolerances(Array.isArray(res.data) ? res.data : [])
    } catch (err) {
      showToast(t('common.error_loading'), 'error')
    } finally {
      setLoading(false)
    }
  }

  const blankForm = {
    name: '', quantity_percent: 0, quantity_absolute: 0,
    price_percent: 0, price_absolute: 0, supplier_id: '', product_category_id: ''
  }

  const handleSave = async (e) => {
    e.preventDefault()
    if (!editing?.name) {
      showToast(t('matching.tol_name_required'), 'error')
      return
    }
    try {
      setSaving(true)
      const payload = {
        ...editing,
        quantity_percent: parseFloat(editing.quantity_percent) || 0,
        quantity_absolute: parseFloat(editing.quantity_absolute) || 0,
        price_percent: parseFloat(editing.price_percent) || 0,
        price_absolute: parseFloat(editing.price_absolute) || 0,
        supplier_id: editing.supplier_id ? parseInt(editing.supplier_id) : null,
        product_category_id: editing.product_category_id ? parseInt(editing.product_category_id) : null,
      }
      await purchasesAPI.saveTolerance(payload)
      showToast(t('matching.tol_saved'), 'success')
      setEditing(null)
      loadTolerances()
    } catch (err) {
      showToast(err.response?.data?.detail || t('common.error'), 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleChange = (field, value) => {
    setEditing(prev => ({ ...prev, [field]: value }))
  }

  if (editing) {
    return (
      <div className="workspace fade-in">
        <div className="workspace-header">
          <BackButton onClick={() => setEditing(null)} />
          <h1 className="workspace-title">
            {editing.id ? t('matching.tol_edit') : t('matching.tol_new')}
          </h1>
        </div>
        <form onSubmit={handleSave}>
          <div className="card mb-4">
            <FormField label={t('matching.tol_name')} required>
              <input
                className="form-input"
                value={editing.name}
                onChange={(e) => handleChange('name', e.target.value)}
                required
              />
            </FormField>

            <div className="form-row">
              <FormField label={t('matching.qty_percent')} style={{ flex: 1 }}>
                <input
                  type="number" step="0.01" min="0" className="form-input"
                  value={editing.quantity_percent}
                  onChange={(e) => handleChange('quantity_percent', e.target.value)}
                />
              </FormField>
              <FormField label={t('matching.qty_absolute')} style={{ flex: 1 }}>
                <input
                  type="number" step="0.0001" min="0" className="form-input"
                  value={editing.quantity_absolute}
                  onChange={(e) => handleChange('quantity_absolute', e.target.value)}
                />
              </FormField>
            </div>

            <div className="form-row">
              <FormField label={t('matching.price_percent')} style={{ flex: 1 }}>
                <input
                  type="number" step="0.01" min="0" className="form-input"
                  value={editing.price_percent}
                  onChange={(e) => handleChange('price_percent', e.target.value)}
                />
              </FormField>
              <FormField label={t('matching.price_absolute')} style={{ flex: 1 }}>
                <input
                  type="number" step="0.0001" min="0" className="form-input"
                  value={editing.price_absolute}
                  onChange={(e) => handleChange('price_absolute', e.target.value)}
                />
              </FormField>
            </div>

            <div className="form-row">
              <FormField label={t('matching.supplier_override')} style={{ flex: 1 }}>
                <input
                  type="number" className="form-input"
                  value={editing.supplier_id}
                  onChange={(e) => handleChange('supplier_id', e.target.value)}
                  placeholder={t('matching.optional')}
                />
              </FormField>
              <FormField label={t('matching.category_override')} style={{ flex: 1 }}>
                <input
                  type="number" className="form-input"
                  value={editing.product_category_id}
                  onChange={(e) => handleChange('product_category_id', e.target.value)}
                  placeholder={t('matching.optional')}
                />
              </FormField>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button className="btn btn-primary" type="submit" disabled={saving}>
              {t('common.save')}
            </button>
            <button className="btn btn-outline" type="button" onClick={() => setEditing(null)}>
              {t('common.cancel')}
            </button>
          </div>
        </form>
      </div>
    )
  }

  return (
    <div className="workspace fade-in">
      <div className="workspace-header">
        <BackButton />
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 className="workspace-title">{t('matching.tolerances')}</h1>
            <p className="workspace-subtitle">{t('matching.tol_subtitle')}</p>
          </div>
          <button className="btn btn-primary" onClick={() => setEditing({ ...blankForm })}>
            + {t('matching.tol_new')}
          </button>
        </div>
      </div>

      <DataTable
          columns={[
            { key: 'name', label: t('matching.tol_name'), style: { fontWeight: '600' } },
            { key: 'quantity_percent', label: t('matching.qty_percent'), headerStyle: { textAlign: 'center' }, style: { textAlign: 'center' }, render: (val) => `${val}%` },
            { key: 'quantity_absolute', label: t('matching.qty_absolute'), headerStyle: { textAlign: 'center' }, style: { textAlign: 'center' } },
            { key: 'price_percent', label: t('matching.price_percent'), headerStyle: { textAlign: 'center' }, style: { textAlign: 'center' }, render: (val) => `${val}%` },
            { key: 'price_absolute', label: t('matching.price_absolute'), headerStyle: { textAlign: 'center' }, style: { textAlign: 'center' } },
            { key: 'id', label: t('common.actions'), render: (val, row) => (
              <button className="btn btn-sm btn-outline-primary" onClick={() => setEditing({ ...row })}>
                {t('common.edit')}
              </button>
            )},
          ]}
          data={tolerances}
          loading={loading}
          emptyTitle={t('matching.no_tolerances')}
          emptyAction={{ label: t('matching.tol_new'), onClick: () => setEditing({ ...blankForm }) }}
        />
    </div>
  )
}
