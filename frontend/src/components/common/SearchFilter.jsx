import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Search, X } from 'lucide-react';

/**
 * Shared SearchFilter component — adds consistent search to list pages.
 *
 * Props:
 *   value       — controlled search value
 *   onChange     — (value) => void
 *   placeholder  — input placeholder
 *   filters      — [{ key, label, options: [{ value, label }] }] for dropdown filters
 *   filterValues — { [key]: value } controlled filter state
 *   onFilterChange — (key, value) => void
 */
export default function SearchFilter({
    value = '',
    onChange,
    placeholder,
    filters = [],
    filterValues = {},
    onFilterChange,
}) {
    const { t } = useTranslation();

    return (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px 0',
            flexWrap: 'wrap',
        }}>
            <div style={{ position: 'relative', flex: '1 1 280px', maxWidth: '360px' }}>
                <Search size={16} style={{
                    position: 'absolute',
                    right: '12px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--text-secondary)',
                    pointerEvents: 'none',
                }} />
                <input
                    type="text"
                    className="form-input"
                    placeholder={placeholder || t('common.search', 'بحث...')}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    style={{ paddingRight: '36px' }}
                />
                {value && (
                    <button
                        onClick={() => onChange('')}
                        style={{
                            position: 'absolute',
                            left: '8px',
                            top: '50%',
                            transform: 'translateY(-50%)',
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            color: 'var(--text-secondary)',
                            padding: '2px',
                        }}
                    >
                        <X size={14} />
                    </button>
                )}
            </div>
            {filters.map((filter) => (
                <select
                    key={filter.key}
                    className="form-input"
                    value={filterValues[filter.key] || ''}
                    onChange={(e) => onFilterChange(filter.key, e.target.value)}
                    style={{ flex: '0 0 auto', width: 'auto', minWidth: '140px' }}
                >
                    <option value="">{filter.label}</option>
                    {filter.options.map((opt) => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                </select>
            ))}
        </div>
    );
}
