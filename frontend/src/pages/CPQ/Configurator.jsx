import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router-dom';
import { cpqAPI } from '../../utils/api';
import { Check, ShoppingCart, AlertTriangle } from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';
import { useToast } from '../../context/ToastContext';
import { formatNumber } from '../../utils/format';
import DateInput from '../../components/common/DateInput';
import { PageLoading } from '../../components/common/LoadingStates'

const Configurator = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const { configId } = useParams();
    const navigate = useNavigate();
    const { showToast } = useToast();
    const [config, setConfig] = useState(null);
    const [loading, setLoading] = useState(true);
    const [selectedOptions, setSelectedOptions] = useState({});
    const [validationResult, setValidationResult] = useState(null);
    const [priceResult, setPriceResult] = useState(null);
    const [quantity, setQuantity] = useState(1);
    const [customerId, setCustomerId] = useState('');
    const [saving, setSaving] = useState(false);
    const [validUntil, setValidUntil] = useState('');

    useEffect(() => {
        cpqAPI.getConfiguration(configId)
            .then(res => {
                const data = res.data;
                setConfig(data);
                // Pre-select defaults
                const defaults = {};
                (data.groups || []).forEach(g => {
                    const def = g.options.find(o => o.is_default);
                    if (def) defaults[g.id] = def.id;
                });
                setSelectedOptions(defaults);
            })
            .catch(() => showToast(t('common.error'), 'error'))
            .finally(() => setLoading(false));
    }, [configId]);

    const allSelectedIds = Object.values(selectedOptions).filter(Boolean).map(Number);

    const handleOptionChange = (groupId, optionId) => {
        setSelectedOptions(prev => ({ ...prev, [groupId]: optionId }));
        setValidationResult(null);
        setPriceResult(null);
    };

    const handleValidate = async () => {
        try {
            const res = await cpqAPI.validateConfig({
                configuration_id: Number(configId),
                selected_option_ids: allSelectedIds,
            });
            setValidationResult(res.data);
            if (res.data.valid) {
                handleCalculatePrice();
            }
        } catch (e) {
            showToast(t('common.error'), 'error');
        }
    };

    const handleCalculatePrice = async () => {
        try {
            const res = await cpqAPI.calculatePrice({
                lines: [{
                    product_id: config.product_id,
                    configuration_id: Number(configId),
                    selected_option_ids: allSelectedIds,
                    quantity: Number(quantity),
                }],
                customer_id: customerId ? Number(customerId) : null,
            });
            setPriceResult(res.data);
        } catch (e) {
            showToast(t('common.error'), 'error');
        }
    };

    const handleCreateQuote = async () => {
        if (!customerId) { alert(t('cpq.select_customer')); return; }
        if (!validUntil) { alert(t('cpq.select_valid_until')); return; }
        setSaving(true);
        try {
            const res = await cpqAPI.createQuote({
                customer_id: Number(customerId),
                valid_until: validUntil,
                lines: [{
                    product_id: config.product_id,
                    configuration_id: Number(configId),
                    selected_option_ids: allSelectedIds,
                    quantity: Number(quantity),
                }],
            });
            navigate(`/sales/cpq/quotes/${res.data.id}`);
        } catch (e) {
            alert(e.response?.data?.detail || 'Error');
        }
        setSaving(false);
    };

    if (loading) return <PageLoading />;
    if (!config) return <div className="empty-state">{t('cpq.config_not_found')}</div>;

    return (
        <div className="module-container" dir={isRTL ? 'rtl' : 'ltr'}>
            <BackButton />
            <div className="module-header">
                <h1>{t('cpq.configurator')}: {config.product_name}</h1>
            </div>
            <p style={{ color: '#6b7280', marginBottom: 24 }}>{config.name} — {t('cpq.base_price')}: {formatNumber(config.selling_price || 0)}</p>

            {/* Step-by-step option groups */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20, marginBottom: 24 }}>
                {(config.groups || []).map((g, idx) => (
                    <div key={g.id} className="card" style={{ padding: 16, border: '1px solid #e5e7eb', borderRadius: 8 }}>
                        <h3 style={{ marginBottom: 8 }}>
                            {t('cpq.step')} {idx + 1}: {g.name}
                            {g.is_required && <span style={{ color: '#ef4444', marginLeft: 4 }}>*</span>}
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {g.options.map(o => (
                                <label key={o.id} style={{
                                    display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px',
                                    borderRadius: 6, cursor: 'pointer',
                                    border: selectedOptions[g.id] === o.id ? '2px solid #2563eb' : '1px solid #d1d5db',
                                    background: selectedOptions[g.id] === o.id ? '#eff6ff' : '#fff',
                                }}>
                                    <input
                                        type="radio"
                                        name={`group-${g.id}`}
                                        checked={selectedOptions[g.id] === o.id}
                                        onChange={() => handleOptionChange(g.id, o.id)}
                                    />
                                    <span style={{ flex: 1 }}>{o.name}</span>
                                    {Number(o.price_adjustment) !== 0 && (
                                        <span style={{ color: Number(o.price_adjustment) > 0 ? '#16a34a' : '#ef4444', fontWeight: 600, fontSize: 13 }}>
                                            {Number(o.price_adjustment) > 0 ? '+' : ''}{formatNumber(o.price_adjustment)}
                                        </span>
                                    )}
                                </label>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            {/* Quantity & Customer */}
            <div style={{ display: 'flex', gap: 16, marginBottom: 20, flexWrap: 'wrap' }}>
                <div>
                    <label className="form-label">{t('cpq.quantity')}</label>
                    <input type="number" min="1" className="form-input" style={{ width: 100 }}
                        value={quantity} onChange={e => { setQuantity(e.target.value); setPriceResult(null); }} />
                </div>
                <div>
                    <label className="form-label">{t('cpq.customer_id')}</label>
                    <input type="number" className="form-input" style={{ width: 120 }
                        } value={customerId} onChange={e => setCustomerId(e.target.value)} placeholder="ID" />
                </div>
                <div>
                    <label className="form-label">{t('cpq.valid_until')}</label>
                    <DateInput className="form-input" value={validUntil} onChange={e => setValidUntil(e.target.value)} />
                </div>
            </div>

            {/* Validate */}
            <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
                <button className="btn btn-secondary" onClick={handleValidate}>
                    <Check size={16} /> {t('cpq.validate_config')}
                </button>
                <button className="btn btn-primary" onClick={handleCalculatePrice}>
                    {t('cpq.calculate_price')}
                </button>
            </div>

            {/* Validation result */}
            {validationResult && !validationResult.valid && (
                <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, padding: 16, marginBottom: 20 }}>
                    <h4 style={{ color: '#dc2626', display: 'flex', alignItems: 'center', gap: 6 }}>
                        <AlertTriangle size={18} /> {t('cpq.validation_errors')}
                    </h4>
                    <ul style={{ margin: '8px 0 0 16px', color: '#991b1b' }}>
                        {validationResult.errors.map((e, i) => <li key={i}>{e.message}</li>)}
                    </ul>
                </div>
            )}
            {validationResult && validationResult.valid && (
                <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 8, padding: 12, marginBottom: 20, color: '#166534' }}>
                    <Check size={16} /> {t('cpq.config_valid')}
                </div>
            )}

            {/* Price preview */}
            {priceResult && (
                <div className="card" style={{ padding: 20, marginBottom: 24, border: '1px solid #e5e7eb', borderRadius: 8 }}>
                    <h3 style={{ marginBottom: 12 }}>{t('cpq.price_preview')}</h3>
                    {priceResult.lines?.map((l, i) => (
                        <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 12, marginBottom: 8 }}>
                            <div><span style={{ color: '#6b7280', fontSize: 12 }}>{t('cpq.base_price')}</span><div style={{ fontWeight: 600 }}>{formatNumber(l.base_unit_price)}</div></div>
                            <div><span style={{ color: '#6b7280', fontSize: 12 }}>{t('cpq.option_adjustments')}</span><div style={{ fontWeight: 600 }}>{formatNumber(l.option_adjustments)}</div></div>
                            <div><span style={{ color: '#6b7280', fontSize: 12 }}>{t('cpq.discount')}</span><div style={{ fontWeight: 600, color: '#dc2626' }}>-{formatNumber(l.discount_applied)}</div></div>
                            <div><span style={{ color: '#6b7280', fontSize: 12 }}>{t('cpq.unit_price')}</span><div style={{ fontWeight: 600 }}>{formatNumber(l.final_unit_price)}</div></div>
                        </div>
                    ))}
                    <hr style={{ margin: '12px 0' }} />
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 16 }}>
                        <span>{t('cpq.quantity')}: {quantity}</span>
                        <span style={{ fontWeight: 700, color: '#2563eb' }}>{t('cpq.total')}: {formatNumber(priceResult.final_amount)}</span>
                    </div>
                </div>
            )}

            {/* Create Quote */}
            <button className="btn btn-success" onClick={handleCreateQuote} disabled={saving || !priceResult}>
                <ShoppingCart size={16} /> {saving ? t('common.saving') : t('cpq.create_quote')}
            </button>
        </div>
    );
};

export default Configurator;
