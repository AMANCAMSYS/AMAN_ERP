import React from 'react';
import DatePicker, { registerLocale } from 'react-datepicker';
import { arSA } from 'date-fns/locale';
import 'react-datepicker/dist/react-datepicker.css';
import { toInputDate } from '../../utils/dateUtils';
import { useTranslation } from 'react-i18next';
import { Calendar } from 'lucide-react';

// Register Arabic locale
registerLocale('ar-sa', arSA);

const CustomDatePicker = ({
    selected,
    onChange,
    placeholder,
    label,
    name,
    id,
    required = false,
    className = "",
    isClearable = true
}) => {
    const { i18n } = useTranslation();
    const isRtl = i18n.dir() === 'rtl';

    const handleChange = (date) => {
        // Format to YYYY-MM-DD for consistency with backend/state
        const formattedDate = date ? toInputDate(date) : '';
        onChange(formattedDate, date);
    };

    return (
        <div className={`custom-datepicker-container ${className}`}>
            {label && <label htmlFor={id} className="form-label">{label}{required && <span style={{ color: 'var(--danger, #ef4444)' }}> *</span>}</label>}
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <div style={{
                    position: 'absolute',
                    [isRtl ? 'left' : 'right']: (isClearable && selected) ? '34px' : '10px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    zIndex: 2,
                    pointerEvents: 'none',
                    color: 'var(--text-muted, #9ca3af)',
                    display: 'flex',
                    alignItems: 'center',
                    transition: 'left 0.2s ease, right 0.2s ease',
                }}>
                    <Calendar size={16} />
                </div>
                <DatePicker
                    id={id}
                    name={name}
                    selected={selected ? new Date(selected) : null}
                    onChange={handleChange}
                    dateFormat="yyyy/MM/dd"
                    locale="ar-sa"
                    placeholderText={placeholder || "YYYY/MM/DD"}
                    className="form-input w-full"
                    isClearable={isClearable}
                    autoComplete="off"
                    portalId="datepicker-portal"
                    popperPlacement="bottom-start"
                />
            </div>
        </div>
    );
};

export default CustomDatePicker;
