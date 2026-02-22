import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft } from 'lucide-react';

/**
 * Consistent back button for sub-pages.
 * Place inside workspace-header, before the title div.
 * Always uses navigate(-1) so it goes back to wherever the user came from.
 * 
 * @param {function} [onClick] - Custom click handler (overrides default navigate(-1))
 * @param {string} [label] - Optional tooltip label
 */
export default function BackButton({ onClick, label }) {
    const navigate = useNavigate();
    const { i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';

    return (
        <button
            onClick={() => onClick ? onClick() : navigate(-1)}
            title={label || (isRTL ? 'رجوع' : 'Back')}
            className="back-button"
            style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                border: '1px solid var(--border-color, #e5e7eb)',
                background: 'var(--bg-primary, #fff)',
                cursor: 'pointer',
                color: 'var(--text-secondary, #6b7280)',
                transition: 'all 0.2s ease',
                flexShrink: 0,
            }}
            onMouseEnter={e => {
                e.currentTarget.style.background = 'var(--primary, #4f46e5)';
                e.currentTarget.style.color = '#fff';
                e.currentTarget.style.borderColor = 'var(--primary, #4f46e5)';
            }}
            onMouseLeave={e => {
                e.currentTarget.style.background = 'var(--bg-primary, #fff)';
                e.currentTarget.style.color = 'var(--text-secondary, #6b7280)';
                e.currentTarget.style.borderColor = 'var(--border-color, #e5e7eb)';
            }}
        >
            <ArrowLeft size={18} style={isRTL ? { transform: 'rotate(180deg)' } : undefined} />
        </button>
    );
}
