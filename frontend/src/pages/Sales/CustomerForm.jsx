import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { salesAPI } from '../../utils/api'
import { useTranslation } from 'react-i18next'
import { useBranch } from '../../context/BranchContext'

function CustomerForm() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { currentBranch } = useBranch()
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [formData, setFormData] = useState({
        name: '',
        name_en: '',
        email: '',
        phone: '',
        tax_number: '',
        address: '',
        credit_limit: 0
    })

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError(null)

        try {
            // Sanitize payload
            const payload = {
                ...formData,
                name_en: formData.name_en || null,
                email: formData.email || null,
                phone: formData.phone || null,
                tax_number: formData.tax_number || null,
                address: formData.address || null,
                branch_id: currentBranch?.id
            }
            await salesAPI.createCustomer(payload)
            navigate('/sales/customers')
        } catch (err) {
            console.error(err)
            const errMsg = err.response?.data?.detail
            setError(typeof errMsg === 'string' ? errMsg : JSON.stringify(errMsg) || t('sales.customers.form.error_add'))
        } finally {
            setLoading(false)
        }
    }

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value })
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <h1 className="workspace-title">{t('sales.customers.form.create_title')}</h1>
                <p className="workspace-subtitle">{t('sales.customers.form.create_subtitle')}</p>
            </div>

            <div className="card" style={{ maxWidth: '800px' }}>
                {error && <div className="alert alert-error mb-4">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="form-section">
                        <h3 className="section-title">{t('sales.customers.form.basic_info')}</h3>
                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">{t('sales.customers.form.name_ar')} *</label>
                                <input
                                    type="text" name="name" className="form-input" required
                                    value={formData.name} onChange={handleChange}
                                    placeholder={t('sales.customers.form.name_ar')}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('sales.customers.form.name_en')}</label>
                                <input
                                    type="text" name="name_en" className="form-input"
                                    value={formData.name_en} onChange={handleChange}
                                    placeholder="e.g. Al-Noor Trading"
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">{t('sales.customers.form.tax_number')}</label>
                                <input
                                    type="text" name="tax_number" className="form-input"
                                    value={formData.tax_number} onChange={handleChange}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('sales.customers.form.credit_limit')}</label>
                                <input
                                    type="number" name="credit_limit" className="form-input"
                                    value={formData.credit_limit} onChange={handleChange}
                                />
                            </div>
                        </div>
                    </div>

                    <div className="form-section">
                        <h3 className="section-title">{t('sales.customers.form.contact_info')}</h3>
                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">{t('sales.customers.form.phone')}</label>
                                <input
                                    type="tel" name="phone" className="form-input"
                                    value={formData.phone} onChange={handleChange}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('sales.customers.form.email')}</label>
                                <input
                                    type="email" name="email" className="form-input"
                                    value={formData.email} onChange={handleChange}
                                />
                            </div>
                        </div>
                        <div className="form-group">
                            <label className="form-label">{t('sales.customers.form.address')}</label>
                            <textarea
                                name="address" className="form-input" rows="3"
                                value={formData.address} onChange={handleChange}
                            ></textarea>
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                        <button type="submit" className="btn btn-primary" disabled={loading}>
                            {loading ? t('sales.customers.form.saving') : t('sales.customers.form.save_btn')}
                        </button>
                        <button type="button" className="btn btn-secondary" onClick={() => navigate('/sales/customers')}>
                            {t('common.cancel')}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}

export default CustomerForm
