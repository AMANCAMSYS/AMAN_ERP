import React from 'react';
import { useTranslation } from 'react-i18next';
import { Calendar, Clock, CalendarDays, CalendarRange } from 'lucide-react';

/**
 * PeriodSelector — period selector for KPI dashboards.
 * محدد الفترة الزمنية للوحات الأداء
 *
 * Props:
 *   value         — current period key (today|wtd|mtd|qtd|ytd|custom)
 *   onChange      — (period, startDate?, endDate?) => void
 *   startDate     — for custom period
 *   endDate       — for custom period
 *   showCustom    — show custom date range picker (default true)
 */

const PERIODS = [
    { key: 'today', icon: Clock,          color: '#6366f1' },
    { key: 'wtd',   icon: CalendarDays,   color: '#8b5cf6' },
    { key: 'mtd',   icon: Calendar,       color: '#3b82f6' },
    { key: 'qtd',   icon: CalendarRange,  color: '#0ea5e9' },
    { key: 'ytd',   icon: CalendarRange,  color: '#14b8a6' },
];

const PeriodSelector = ({
    value = 'mtd',
    onChange,
    startDate,
    endDate,
    showCustom = true,
}) => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.dir() === 'rtl';

    const labels = {
        today: isRTL ? 'اليوم' : 'Today',
        wtd:   isRTL ? 'الأسبوع' : 'Week',
        mtd:   isRTL ? 'الشهر' : 'Month',
        qtd:   isRTL ? 'الربع' : 'Quarter',
        ytd:   isRTL ? 'السنة' : 'Year',
        custom: isRTL ? 'مخصص' : 'Custom',
    };

    return (
        <div style={{
            display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap',
        }}>
            {PERIODS.map(p => {
                const active = value === p.key;
                const Icon = p.icon;
                return (
                    <button
                        key={p.key}
                        onClick={() => onChange(p.key)}
                        style={{
                            display: 'flex', alignItems: 'center', gap: '4px',
                            padding: '5px 12px',
                            fontSize: '0.78rem', fontWeight: active ? 700 : 500,
                            border: `1px solid ${active ? p.color + '66' : 'var(--border-color)'}`,
                            borderRadius: '8px',
                            background: active ? p.color + '12' : 'var(--bg-card)',
                            color: active ? p.color : 'var(--text-secondary)',
                            cursor: 'pointer',
                            transition: 'all .15s',
                        }}
                    >
                        <Icon size={13} />
                        {labels[p.key]}
                    </button>
                );
            })}

            {showCustom && (
                <>
                    <button
                        onClick={() => onChange('custom', startDate, endDate)}
                        style={{
                            display: 'flex', alignItems: 'center', gap: '4px',
                            padding: '5px 12px',
                            fontSize: '0.78rem', fontWeight: value === 'custom' ? 700 : 500,
                            border: `1px solid ${value === 'custom' ? '#f97316' + '66' : 'var(--border-color)'}`,
                            borderRadius: '8px',
                            background: value === 'custom' ? '#f9731612' : 'var(--bg-card)',
                            color: value === 'custom' ? '#f97316' : 'var(--text-secondary)',
                            cursor: 'pointer',
                        }}
                    >
                        <CalendarRange size={13} />
                        {labels.custom}
                    </button>

                    {value === 'custom' && (
                        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                            <input
                                type="date"
                                value={startDate || ''}
                                onChange={e => onChange('custom', e.target.value, endDate)}
                                style={{
                                    padding: '4px 8px', borderRadius: '6px',
                                    border: '1px solid var(--border-color)', fontSize: '0.78rem',
                                    background: 'var(--bg-card)', color: 'var(--text-main)',
                                }}
                            />
                            <span style={{ color: '#94a3b8', fontSize: '0.75rem' }}>→</span>
                            <input
                                type="date"
                                value={endDate || ''}
                                onChange={e => onChange('custom', startDate, e.target.value)}
                                style={{
                                    padding: '4px 8px', borderRadius: '6px',
                                    border: '1px solid var(--border-color)', fontSize: '0.78rem',
                                    background: 'var(--bg-card)', color: 'var(--text-main)',
                                }}
                            />
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default PeriodSelector;
