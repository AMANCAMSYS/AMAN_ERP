import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Eye, FileText } from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';

const QuoteList = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const navigate = useNavigate();
    const [quotes, setQuotes] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // List quotes via products endpoint filtered as needed
        // For now, no list endpoint — use a simple fetch approach
        setLoading(false);
    }, []);

    // Since we don't have a list-all-quotes endpoint, use navigate from detail
    return (
        <div className="module-container" dir={isRTL ? 'rtl' : 'ltr'}>
            <BackButton />
            <div className="module-header">
                <h1><FileText size={24} /> {t('cpq.quotes_title')}</h1>
                <button className="btn btn-primary" onClick={() => navigate('/sales/cpq/products')}>
                    {t('cpq.new_quote')}
                </button>
            </div>

            <div style={{ textAlign: 'center', padding: 40, color: '#6b7280' }}>
                <p>{t('cpq.quote_search_hint')}</p>
                <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: 16 }}>
                    <input
                        type="number"
                        placeholder={t('cpq.quote_id_placeholder')}
                        id="quote-id-input"
                        className="form-input"
                        style={{ width: 160 }}
                        onKeyDown={e => {
                            if (e.key === 'Enter' && e.target.value) {
                                navigate(`/sales/cpq/quotes/${e.target.value}`);
                            }
                        }}
                    />
                    <button className="btn btn-primary" onClick={() => {
                        const v = document.getElementById('quote-id-input')?.value;
                        if (v) navigate(`/sales/cpq/quotes/${v}`);
                    }}>
                        <Eye size={14} /> {t('cpq.view_quote')}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default QuoteList;
