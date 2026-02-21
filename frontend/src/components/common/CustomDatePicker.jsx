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
            {label && <label htmlFor={id} className="form-label">{label}{required && <span className="text-red-500"> *</span>}</label>}
            <div className="relative flex items-center">
                <div className={`absolute ${isRtl ? 'left-3' : 'right-3'} z-10 text-base-content/40`}>
                    <Calendar size={18} />
                </div>
                <DatePicker
                    id={id}
                    name={name}
                    selected={selected ? new Date(selected) : null}
                    onChange={handleChange}
                    dateFormat="yyyy/MM/dd"
                    locale="ar-sa"
                    placeholderText={placeholder || "YYYY/MM/DD"}
                    className="form-input w-full pr-10"
                    isClearable={isClearable}
                    autoComplete="off"
                />
            </div>
        </div>
    );
};

export default CustomDatePicker;
