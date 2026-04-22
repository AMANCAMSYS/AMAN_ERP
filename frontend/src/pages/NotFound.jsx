import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const NotFound = () => {
    const navigate = useNavigate();
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '70vh',
            textAlign: 'center',
            direction: isRTL ? 'rtl' : 'ltr',
            padding: '2rem'
        }}>
            <div style={{
                fontSize: '8rem',
                fontWeight: '800',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                lineHeight: '1',
                marginBottom: '1rem'
            }}>
                404
            </div>
            <h2 style={{
                fontSize: '1.5rem',
                color: 'var(--text-primary, #333)',
                marginBottom: '0.5rem'
            }}>
                {t('common.page_not_found')}
            </h2>
            <p style={{
                color: 'var(--text-secondary, #666)',
                marginBottom: '2rem',
                maxWidth: '400px'
            }}>
                {t('common.page_not_found_desc')}
            </p>
            <button
                onClick={() => navigate('/dashboard')}
                style={{
                    padding: '0.75rem 2rem',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '1rem',
                    cursor: 'pointer',
                    transition: 'opacity 0.2s, transform 0.2s',
                }}
                onMouseOver={(e) => { e.target.style.opacity = '0.9'; e.target.style.transform = 'translateY(-1px)'; }}
                onMouseOut={(e) => { e.target.style.opacity = '1'; e.target.style.transform = 'translateY(0)'; }}
            >
                {t('common.back_to_dashboard')}
            </button>
        </div>
    );
};

export default NotFound;
