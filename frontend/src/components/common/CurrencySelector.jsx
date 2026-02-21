import { useState, useEffect } from 'react'
import { currenciesAPI } from '../../utils/api'
import { useTranslation } from 'react-i18next'

export default function CurrencySelector({ value, onChange, className = '', label = '', disabled = false, required = false }) {
    const { t } = useTranslation()
    const [currencies, setCurrencies] = useState([])
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        const fetchCurrencies = async () => {
            try {
                setLoading(true)
                const response = await currenciesAPI.list()
                setCurrencies(response.data)

                // If no value is selected and we have currencies, select base by default
                if (!value && response.data.length > 0) {
                    const base = response.data.find(c => c.is_base) || response.data[0]
                    if (base) {
                        onChange(base.code, base.exchange_rate || 1.0)
                    }
                }
            } catch (error) {
                console.error('Error fetching currencies:', error)
            } finally {
                setLoading(false)
            }
        }
        fetchCurrencies()
    }, [])

    const handleChange = (e) => {
        const code = e.target.value
        const selected = currencies.find(c => c.code === code)
        onChange(code, selected?.exchange_rate || 1.0)
    }

    if (loading && currencies.length === 0) {
        return <div className="loading loading-sm"></div>
    }

    return (
        <div className={`form-group ${className}`}>
            {label && <label className="form-label">{label}</label>}
            <select
                className="form-input"
                value={value}
                onChange={handleChange}
                disabled={disabled}
                required={required}
            >
                {currencies.map(c => (
                    <option key={c.code} value={c.code}>
                        {c.code} - {c.name} {c.is_base ? `(${t('common.base_currency') || 'العملة الأساسية'})` : ''}
                    </option>
                ))}
            </select>
        </div>
    )
}
