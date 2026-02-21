import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { inventoryAPI, currenciesAPI, purchasesAPI } from '../../utils/api'
import { useTranslation } from 'react-i18next'
import { useBranch } from '../../context/BranchContext'
import { getCurrency } from '../../utils/auth'

function SupplierForm() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { id } = useParams()
    const isEdit = Boolean(id)
    const { currentBranch } = useBranch()
    const [loading, setLoading] = useState(false)
    const [currencies, setCurrencies] = useState([])
    const [error, setError] = useState(null)
    const [formData, setFormData] = useState({
        name: '',
        name_en: '',
        email: '',
        phone: '',
        tax_number: '',
        address: '',
        currency: getCurrency()
    })

    useEffect(() => {
        const fetchSupplierData = async () => {
            if (!isEdit) return
            try {
                setLoading(true)
                const response = await inventoryAPI.getSupplier(id)
                const s = response.data
                setFormData({
                    name: s.name || '',
                    name_en: s.name_en || '',
                    email: s.email || '',
                    phone: s.phone || '',
                    tax_number: s.tax_number || '',
                    address: s.address || '',
                    currency: s.currency || getCurrency()
                })
            } catch (err) {
                setError(t('common.error_loading'))
            } finally {
                setLoading(false)
            }
        }

        const fetchCurrencies = async () => {
            try {
                const res = await currenciesAPI.list()
                if (res.data) setCurrencies(res.data.filter(c => c.is_active))
            } catch (err) {
                console.error("Failed to fetch currencies", err)
            }
        }
        fetchSupplierData()
        fetchCurrencies()
    }, [id, isEdit, currentBranch?.id, t])

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError(null)

        try {
            if (isEdit) {
                await inventoryAPI.updateSupplier(id, { ...formData, branch_id: currentBranch?.id })
            } else {
                await inventoryAPI.createSupplier({ ...formData, branch_id: currentBranch?.id })
            }
            navigate(isEdit ? `/buying/suppliers/${id}` : '/buying/suppliers')
        } catch (err) {
            setError(err.response?.data?.detail || t('common.error_saving'))
        } finally {
            setLoading(false)
        }
    }

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value })
    }

    const handleDelete = async () => {
        if (!window.confirm(t('buying.suppliers.delete_confirm'))) return
        try {
            await inventoryAPI.deleteSupplier(id)
            navigate('/buying/suppliers')
        } catch (err) {
            const errorMsg = err.response?.data?.detail || t('common.error_deleting')
            alert(errorMsg)
        }
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <h1 className="workspace-title">{isEdit ? t('buying.suppliers.form.title_edit') : t('buying.suppliers.form.title_new')}</h1>
            </div>

            <div className="card" style={{ maxWidth: '800px' }}>
                {error && <div className="alert alert-error mb-4">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="form-section">
                        <h3 className="section-title">{t('buying.suppliers.form.basic_info')}</h3>
                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">{t('buying.suppliers.form.name_ar')} *</label>
                                <input
                                    type="text" name="name" className="form-input" required
                                    value={formData.name} onChange={handleChange}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('buying.suppliers.form.name_en')}</label>
                                <input
                                    type="text" name="name_en" className="form-input"
                                    value={formData.name_en} onChange={handleChange}
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">{t('buying.suppliers.form.tax_number')}</label>
                                <input
                                    type="text" name="tax_number" className="form-input"
                                    value={formData.tax_number} onChange={handleChange}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('common.currency')}</label>
                                <select
                                    name="currency"
                                    className="form-input"
                                    value={formData.currency}
                                    onChange={handleChange}
                                >
                                    {currencies.map(c => (
                                        <option key={c.id} value={c.code}>
                                            {c.name} ({c.code})
                                        </option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </div>

                    <div className="form-section">
                        <h3 className="section-title">{t('buying.suppliers.form.contact_info')}</h3>
                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">{t('buying.suppliers.form.phone')}</label>
                                <input
                                    type="tel" name="phone" className="form-input"
                                    value={formData.phone} onChange={handleChange}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('buying.suppliers.form.email')}</label>
                                <input
                                    type="email" name="email" className="form-input"
                                    value={formData.email} onChange={handleChange}
                                />
                            </div>
                        </div>
                        <div className="form-group">
                            <label className="form-label">{t('buying.suppliers.form.address')}</label>
                            <textarea
                                name="address" className="form-input" rows="3"
                                value={formData.address} onChange={handleChange}
                            ></textarea>
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                        <button type="submit" className="btn btn-primary" disabled={loading}>
                            {loading ? t('buying.suppliers.form.saving') : t('buying.suppliers.form.submit')}
                        </button>
                        <button type="button" className="btn btn-secondary" onClick={() => navigate('/buying/suppliers')}>
                            {t('buying.suppliers.form.cancel')}
                        </button>
                        {isEdit && (
                            <button type="button" className="btn btn-danger" onClick={handleDelete} style={{ marginRight: 'auto' }}>
                                {t('common.delete')}
                            </button>
                        )}
                    </div>
                </form>
            </div>
        </div>
    )
}

export default SupplierForm
