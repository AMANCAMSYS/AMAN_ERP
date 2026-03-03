/**
 * IndustryWidgets — ويدجتات مخصصة حسب نوع النشاط
 * يُعرض في لوحة التحكم فوق الإحصاءات العامة
 */
import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import api from '../../services/apiClient'

const INDUSTRY_META = {
  retail:       { icon: '🛍️', color: '#10B981' },
  wholesale:    { icon: '📦', color: '#0EA5E9' },
  restaurant:   { icon: '🍽️', color: '#EF4444' },
  manufacturing:{ icon: '🏭', color: '#6366f1' },
  construction: { icon: '🏗️', color: '#F59E0B' },
  services:     { icon: '💼', color: '#8B5CF6' },
  pharmacy:     { icon: '💊', color: '#10B981' },
  workshop:     { icon: '🔧', color: '#6B7280' },
  ecommerce:    { icon: '🛒', color: '#3B82F6' },
  logistics:    { icon: '🚛', color: '#14B8A6' },
  agriculture:  { icon: '🌾', color: '#65A30D' },
  general:      { icon: '🌐', color: '#94A3B8' },
}

export default function IndustryWidgets() {
  const { t, i18n } = useTranslation()
  const isRTL = i18n.language === 'ar'
  const [widgets, setWidgets] = useState([])
  const [industryType, setIndustryType] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchWidgets = async () => {
      try {
        const res = await api.get('/dashboard/industry-widgets')
        setWidgets(res.data?.widgets || [])
        setIndustryType(res.data?.industry_type || null)
      } catch (err) {
        console.warn('Industry widgets not available:', err.message)
      } finally {
        setLoading(false)
      }
    }
    fetchWidgets()
  }, [])

  if (loading || !industryType || industryType === 'general' || widgets.length === 0) {
    return null
  }

  const meta = INDUSTRY_META[industryType] || INDUSTRY_META.general
  const industryLabel = isRTL
    ? t(`industry_types.${industryType}`, industryType)
    : t(`industry_types.${industryType}`, industryType)

  return (
    <div style={{
      marginBottom: '20px',
      background: `linear-gradient(135deg, ${meta.color}15 0%, ${meta.color}08 100%)`,
      border: `1px solid ${meta.color}30`,
      borderRadius: 'var(--radius, 12px)',
      padding: '16px 20px',
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        marginBottom: '12px',
        fontSize: '14px',
        fontWeight: '600',
        color: meta.color,
      }}>
        <span style={{ fontSize: '20px' }}>{meta.icon}</span>
        {industryLabel}
      </div>
      <div style={{
        display: 'grid',
        gridTemplateColumns: `repeat(auto-fill, minmax(200px, 1fr))`,
        gap: '12px',
      }}>
        {widgets.map((w, idx) => (
          <div key={idx} style={{
            background: 'var(--bg-primary, white)',
            borderRadius: '10px',
            padding: '14px 16px',
            border: '1px solid var(--border-color, #e2e8f0)',
            display: 'flex',
            flexDirection: 'column',
            gap: '4px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary, #64748b)' }}>
                {isRTL ? w.label_ar : w.label_en}
              </span>
              <span style={{ fontSize: '16px' }}>{w.icon}</span>
            </div>
            <div style={{
              fontSize: '22px',
              fontWeight: '700',
              color: w.alert ? '#EF4444' : 'var(--text-primary, #1e293b)',
            }}>
              {typeof w.value === 'number' && w.value > 999
                ? w.value.toLocaleString()
                : w.value}
              {w.target && (
                <span style={{ fontSize: '12px', color: '#94a3b8', fontWeight: '400', marginInlineStart: '6px' }}>
                  / {w.target}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
