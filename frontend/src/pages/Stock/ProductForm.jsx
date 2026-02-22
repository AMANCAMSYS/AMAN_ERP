import { useNavigate, useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { inventoryAPI, settingsAPI } from '../../utils/api'
import { getCurrency, hasPermission } from '../../utils/auth'
import { useBranch } from '../../context/BranchContext'
import { getStep } from '../../utils/format'
import BackButton from '../../components/common/BackButton';

function ProductForm() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { id } = useParams()
    const { currentBranch } = useBranch()
    const currency = getCurrency()
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [formData, setFormData] = useState({
        item_code: '',
        item_name: '',
        item_name_en: '',
        item_type: 'product',
        unit: t('stock.products.unit_piece'),
        selling_price: '',
        buying_price: '',
        tax_rate: 15,
        description: '',
        category_id: '',
        has_batch_tracking: false,
        has_serial_tracking: false,
        has_expiry_tracking: false,
        shelf_life_days: '',
        expiry_alert_days: 30
    })
    const [categories, setCategories] = useState([])
    useEffect(() => {
        const fetchInitialData = async () => {
            try {
                // Fetch Categories
                const catRes = await inventoryAPI.listCategories({ branch_id: currentBranch?.id })
                setCategories(catRes.data)

                // If new product, fetch default tax rate from settings
                if (!id) {
                    try {
                        const settingsRes = await settingsAPI.get()
                        if (settingsRes.data && settingsRes.data.vat_rate) {
                            setFormData(prev => ({ ...prev, tax_rate: parseFloat(settingsRes.data.vat_rate) }))
                        }
                    } catch (err) {
                        console.warn("Failed to load settings", err)
                    }
                }
            } catch (err) {
                console.error("Failed to load initial data", err)
            }
        }
        fetchInitialData()

        if (id) {
            const fetchProduct = async () => {
                try {
                    setLoading(true)
                    const res = await inventoryAPI.getProduct(id)
                    const data = res.data
                    setFormData({
                        ...data,
                        category_id: data.category_id || '',
                        tax_rate: data.tax_rate ?? 15
                    })
                } catch (err) {
                    setError(t('stock.products.validation.error_load_data'))
                    console.error(err)
                } finally {
                    setLoading(false)
                }
            }
            fetchProduct()
        }
    }, [id, currentBranch, t])

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError(null)

        try {
            if (id) {
                await inventoryAPI.updateProduct(id, formData)
            } else {
                await inventoryAPI.createProduct(formData)
            }
            navigate('/stock/products')
        } catch (err) {
            setError(err.response?.data?.detail || t('stock.products.validation.error_save'))
        } finally {
            setLoading(false)
        }
    }

    const handleChange = (e) => {
        let value = e.target.value

        // Convert number types and category_id to proper types
        if (e.target.type === 'number') {
            value = value === '' ? '' : parseFloat(value)
        } else if (e.target.name === 'category_id' && value !== '') {
            value = parseInt(value)
        }

        setFormData({ ...formData, [e.target.name]: value })
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <h1 className="workspace-title">{id ? t('stock.products.form.edit_title') : t('stock.products.form.title')}</h1>
                <p className="workspace-subtitle">{t('stock.products.form.subtitle')}</p>
            </div>

            <div className="card" style={{ maxWidth: '800px' }}>
                {error && <div className="alert alert-error mb-4">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="form-section">
                        <h3 className="section-title">{t('stock.products.form.basic_info')}</h3>
                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">{t('stock.products.form.code')} *</label>
                                <input
                                    type="text" name="item_code" className="form-input" required
                                    value={formData.item_code} onChange={handleChange}
                                    placeholder={t('stock.products.form.placeholder_code')}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('stock.products.form.type')}</label>
                                <select name="item_type" className="form-input" value={formData.item_type} onChange={handleChange}>
                                    <option value="product">{t('stock.products.form.types.product')}</option>
                                    <option value="service">{t('stock.products.form.types.service')}</option>
                                    <option value="consumable">{t('stock.products.form.types.consumable')}</option>
                                </select>
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">{t('stock.products.form.name_ar')} *</label>
                                <input
                                    type="text" name="item_name" className="form-input" required
                                    value={formData.item_name} onChange={handleChange}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('stock.products.form.name_en')}</label>
                                <input
                                    type="text" name="item_name_en" className="form-input"
                                    value={formData.item_name_en} onChange={handleChange}
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">{t('stock.products.form.unit')}</label>
                                <select name="unit" className="form-input" value={formData.unit} onChange={handleChange}>
                                    <option value="قطعة">{t('stock.products.form.units.piece')}</option>
                                    <option value="كيلو">{t('stock.products.form.units.kg')}</option>
                                    <option value="متر">{t('stock.products.form.units.meter')}</option>
                                    <option value="لتر">{t('stock.products.form.units.liter')}</option>
                                    <option value="علبة">{t('stock.products.form.units.box')}</option>
                                    <option value="كرتون">{t('stock.products.form.units.carton')}</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('stock.products.form.category')} *</label>
                                <select
                                    name="category_id"
                                    className="form-input"
                                    value={formData.category_id}
                                    onChange={handleChange}
                                    required
                                >
                                    <option value="">-- {t('stock.products.form.select_category')} --</option>
                                    {categories.map(cat => (
                                        <option key={cat.id} value={cat.id}>{cat.name}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </div>

                    <div className="form-section">
                        <h3 className="section-title">{t('stock.products.form.pricing')}</h3>
                        <div className="form-row">
                            {hasPermission('stock.view_cost') && (
                                <div className="form-group">
                                    <label className="form-label">{t('stock.products.form.buying_price')} ({currency}) *</label>
                                    <input
                                        type="number" name="buying_price" className="form-input" min="0" step={getStep()}
                                        value={formData.buying_price} onChange={handleChange} required
                                    />
                                </div>
                            )}
                            <div className="form-group">
                                <label className="form-label">{t('stock.products.form.selling_price')} ({currency}) *</label>
                                <input
                                    type="number" name="selling_price" className="form-input" min="0" step={getStep()}
                                    value={formData.selling_price} onChange={handleChange} required
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('stock.products.form.tax_rate')}</label>
                                <input
                                    type="number" name="tax_rate" className="form-input" min="0" max="100"
                                    value={formData.tax_rate} onChange={handleChange}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Tracking Section - only for products */}
                    {formData.item_type === 'product' && (
                        <div className="form-section">
                            <h3 className="section-title">{t('stock.products.form.tracking')}</h3>
                            <div className="form-row">
                                <div className="form-group">
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', padding: '10px', background: formData.has_batch_tracking ? 'var(--primary-light, #e8f0fe)' : 'var(--bg-secondary)', borderRadius: '8px', border: formData.has_batch_tracking ? '2px solid var(--primary)' : '2px solid transparent' }}>
                                        <input type="checkbox" name="has_batch_tracking"
                                            checked={formData.has_batch_tracking}
                                            onChange={(e) => setFormData({ ...formData, has_batch_tracking: e.target.checked })} />
                                        <div>
                                            <strong>📦 {t('stock.products.form.batch_tracking')}</strong>
                                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                                                {t('stock.products.form.batch_tracking_desc')}
                                            </div>
                                        </div>
                                    </label>
                                </div>
                                <div className="form-group">
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', padding: '10px', background: formData.has_serial_tracking ? 'var(--primary-light, #e8f0fe)' : 'var(--bg-secondary)', borderRadius: '8px', border: formData.has_serial_tracking ? '2px solid var(--primary)' : '2px solid transparent' }}>
                                        <input type="checkbox" name="has_serial_tracking"
                                            checked={formData.has_serial_tracking}
                                            onChange={(e) => setFormData({ ...formData, has_serial_tracking: e.target.checked })} />
                                        <div>
                                            <strong>🏷️ {t('stock.products.form.serial_tracking')}</strong>
                                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                                                {t('stock.products.form.serial_tracking_desc')}
                                            </div>
                                        </div>
                                    </label>
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', padding: '10px', background: formData.has_expiry_tracking ? 'var(--primary-light, #e8f0fe)' : 'var(--bg-secondary)', borderRadius: '8px', border: formData.has_expiry_tracking ? '2px solid var(--primary)' : '2px solid transparent' }}>
                                        <input type="checkbox" name="has_expiry_tracking"
                                            checked={formData.has_expiry_tracking}
                                            onChange={(e) => setFormData({ ...formData, has_expiry_tracking: e.target.checked })} />
                                        <div>
                                            <strong>📅 {t('stock.products.form.expiry_tracking')}</strong>
                                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                                                {t('stock.products.form.expiry_tracking_desc')}
                                            </div>
                                        </div>
                                    </label>
                                </div>
                                {formData.has_expiry_tracking && (
                                    <div className="form-group" style={{ display: 'flex', gap: '12px' }}>
                                        <div style={{ flex: 1 }}>
                                            <label className="form-label">{t('stock.products.form.shelf_life')}</label>
                                            <input type="number" name="shelf_life_days" className="form-input" min="0"
                                                value={formData.shelf_life_days} onChange={handleChange} placeholder="365" />
                                        </div>
                                        <div style={{ flex: 1 }}>
                                            <label className="form-label">{t('stock.products.form.expiry_alert')}</label>
                                            <input type="number" name="expiry_alert_days" className="form-input" min="0"
                                                value={formData.expiry_alert_days} onChange={handleChange} placeholder="30" />
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    <div className="form-group">
                        <label className="form-label">{t('stock.products.form.description')}</label>
                        <textarea
                            name="description" className="form-input" rows="3"
                            value={formData.description} onChange={handleChange}
                        ></textarea>
                    </div>

                    <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                        <button type="submit" className="btn btn-primary" disabled={loading}>
                            {loading ? t('stock.products.form.saving') : (id ? t('stock.products.form.save_changes') : t('stock.products.form.save'))}
                        </button>
                        <button type="button" className="btn btn-secondary" onClick={() => navigate('/stock/products')}>
                            {t('stock.products.form.cancel')}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}

export default ProductForm
