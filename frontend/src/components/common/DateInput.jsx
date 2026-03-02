import React from 'react';
import DatePicker, { registerLocale } from 'react-datepicker';
import { arSA } from 'date-fns/locale';
import 'react-datepicker/dist/react-datepicker.css';
import { Calendar } from 'lucide-react';
import { useTranslation } from 'react-i18next';

registerLocale('ar-sa', arSA);

/**
 * DateInput — drop-in replacement for <input type="date">
 * Same API: value="YYYY-MM-DD", onChange(e) => e.target.value = "YYYY-MM-DD"
 * Renders react-datepicker with YYYY/MM/DD display format.
 */
const DateInput = ({
    value,
    onChange,
    className = '',
    placeholder,
    required = false,
    disabled = false,
    min,
    max,
    name,
    id,
    style,
}) => {
    const { i18n } = useTranslation();
    const isRtl = i18n.dir() === 'rtl';

    // Parse YYYY-MM-DD string → Date object for the picker
    const parseDate = (str) => {
        if (!str) return null;
        const d = new Date(str + 'T00:00:00');
        return isNaN(d.getTime()) ? null : d;
    };

    // Format Date → YYYY-MM-DD for state/backend
    const formatForBackend = (date) => {
        if (!date) return '';
        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const d = String(date.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
    };

    const handleChange = (date) => {
        const formatted = formatForBackend(date);
        // Emulate native input event so existing `e.target.value` handlers work
        onChange({ target: { value: formatted, name: name || '' } });
    };

    return (
        <div className="custom-datepicker-container" style={{ position: 'relative', ...style }}>
            <div style={{
                position: 'absolute',
                top: '50%',
                transform: 'translateY(-50%)',
                [isRtl ? 'left' : 'right']: '10px',
                zIndex: 2,
                pointerEvents: 'none',
                color: 'var(--text-muted, #9ca3af)',
                display: 'flex',
                alignItems: 'center'
            }}>
                <Calendar size={16} />
            </div>
            <DatePicker
                id={id}
                name={name}
                selected={parseDate(value)}
                onChange={handleChange}
                dateFormat="yyyy/MM/dd"
                locale="ar-sa"
                placeholderText={placeholder || 'YYYY/MM/DD'}
                className={`form-input ${className}`}
                required={required}
                disabled={disabled}
                autoComplete="off"
                minDate={min ? parseDate(min) : undefined}
                maxDate={max ? parseDate(max) : undefined}
                isClearable={false}
                showYearDropdown
                showMonthDropdown
                dropdownMode="select"
                portalId="datepicker-portal"
                popperPlacement="bottom-start"
            />
        </div>
    );
};

export default DateInput;
