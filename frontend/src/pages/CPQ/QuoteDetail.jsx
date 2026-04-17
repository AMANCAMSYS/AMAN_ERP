import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router-dom';
import { cpqAPI } from '../../utils/api';
import { FileDown, ArrowRightCircle, CheckCircle } from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';
import { useToast } from '../../context/ToastContext';
import { formatNumber } from '../../utils/format';

const QuoteDetail = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const { quoteId } = useParams();
    const navigate = useNavigate();
    const { showToast } = useToast();
    const [quote, setQuote] = useState(null);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);
    const [converting, setConverting] = useState(false);

    const fetchQuote = () => {
        setLoading(true);
        cpqAPI.getQuote(quoteId)
            .then(res => setQuote(res.data))
            .catch(() => showToast(t('common.error'), 'error'))
            .finally(() => setLoading(false));
    };

    useEffect(() => { fetchQuote(); }, [quoteId]);

    const handleGeneratePdf = async () => {
        setGenerating(true);
        try {
            await cpqAPI.generatePdf(quoteId);
            fetchQuote();
            alert(t('cpq.pdf_generated'));
        } catch (e) {
            alert(e.response?.data?.detail || 'Error');
        }
        setGenerating(false);
    };

    const handleConvert = async () => {
        if (!window.confirm(t('cpq.confirm_convert'))) return;
        setConverting(true);
        try {
            const res = await cpqAPI.convertQuote(quoteId);
            alert(`${t('cpq.converted_success')} — ${res.data.sq_number}`);
            fetchQuote();
        } catch (e) {
            alert(e.response?.data?.detail || 'Error');
        }
        setConverting(false);
    };

    const statusBadge = (s) => {
        const colors = { draft: '#6b7280', sent: '#2563eb', accepted: '#16a34a', expired: '#f59e0b', rejected: '#dc2626' };
        return (
            <span style={{ padding: '3px 12px', borderRadius: 12, fontSize: 12, color: '#fff', background: colors[s] || '#6b7280' }}>
                {t(`cpq.status_${s}`, s)}
            </span>
        );
    };

    if (loading) return <div className="loading-spinner">{t('common.loading')}</div>;
    if (!quote) return <div className="empty-state">{t('cpq.quote_not_found')}</div>;

    return (
        <div className="module-container" dir={isRTL ? 'rtl' : 'ltr'}>
            <BackButton />
            <div className="module-header">
                <h1>{t('cpq.quote_detail')} #{quote.id}</h1>
                <div style={{ display: 'flex', gap: 8 }}>
                    <button className="btn btn-secondary" onClick={handleGeneratePdf} disabled={generating}>
                        <FileDown size={16} /> {generating ? t('common.loading') : t('cpq.generate_pdf')}
                    </button>
                    {!quote.quotation_id && quote.status !== 'rejected' && (
                        <button className="btn btn-success" onClick={handleConvert} disabled={converting}>
                            <ArrowRightCircle size={16} /> {converting ? t('common.loading') : t('cpq.convert_to_quotation')}
                        </button>
                    )}
                </div>
            </div>

            {/* Summary cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 24 }}>
                <div className="stat-card">
                    <div className="stat-label">{t('cpq.customer')}</div>
                    <div className="stat-value" style={{ fontSize: 16 }}>{quote.customer_name}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">{t('cpq.status_label')}</div>
                    <div className="stat-value">{statusBadge(quote.status)}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">{t('cpq.valid_until')}</div>
                    <div className="stat-value" style={{ fontSize: 16 }}>{quote.valid_until || '-'}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">{t('cpq.final_amount')}</div>
                    <div className="stat-value" style={{ fontSize: 20, color: '#2563eb' }}>
                        {formatNumber(quote.final_amount || 0)}
                    </div>
                </div>
            </div>

            {quote.quotation_id && (
                <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 8, padding: 12, marginBottom: 20 }}>
                    <CheckCircle size={16} style={{ color: '#16a34a' }} /> {t('cpq.converted_to')} #{quote.quotation_id}
                </div>
            )}

            {quote.pdf_path && (
                <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 8, padding: 12, marginBottom: 20 }}>
                    <FileDown size={16} style={{ color: '#2563eb' }} /> {t('cpq.pdf_available')}
                </div>
            )}

            {/* Line items */}
            <h3 style={{ marginBottom: 12 }}>{t('cpq.line_items')}</h3>
            <div className="table-responsive">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>{t('cpq.product_name')}</th>
                            <th style={{ textAlign: 'right' }}>{t('cpq.quantity')}</th>
                            <th style={{ textAlign: 'right' }}>{t('cpq.base_price')}</th>
                            <th style={{ textAlign: 'right' }}>{t('cpq.option_adjustments')}</th>
                            <th style={{ textAlign: 'right' }}>{t('cpq.discount')}</th>
                            <th style={{ textAlign: 'right' }}>{t('cpq.unit_price')}</th>
                            <th style={{ textAlign: 'right' }}>{t('cpq.line_total')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {(quote.lines || []).map(l => (
                            <tr key={l.id}>
                                <td>{l.product_name}</td>
                                <td style={{ textAlign: 'right' }}>{formatNumber(l.quantity)}</td>
                                <td style={{ textAlign: 'right' }}>{formatNumber(l.base_unit_price)}</td>
                                <td style={{ textAlign: 'right' }}>{formatNumber(l.option_adjustments)}</td>
                                <td style={{ textAlign: 'right', color: '#dc2626' }}>-{formatNumber(l.discount_applied)}</td>
                                <td style={{ textAlign: 'right' }}>{formatNumber(l.final_unit_price)}</td>
                                <td style={{ textAlign: 'right', fontWeight: 600 }}>{formatNumber(l.line_total)}</td>
                            </tr>
                        ))}
                    </tbody>
                    <tfoot>
                        <tr style={{ fontWeight: 600 }}>
                            <td colSpan={5}></td>
                            <td style={{ textAlign: 'right' }}>{t('cpq.subtotal')}</td>
                            <td style={{ textAlign: 'right' }}>{formatNumber(quote.total_amount || 0)}</td>
                        </tr>
                        <tr style={{ color: '#dc2626' }}>
                            <td colSpan={5}></td>
                            <td style={{ textAlign: 'right' }}>{t('cpq.discount')}</td>
                            <td style={{ textAlign: 'right' }}>-{formatNumber(quote.discount_total || 0)}</td>
                        </tr>
                        <tr style={{ fontWeight: 700, fontSize: 16, color: '#2563eb' }}>
                            <td colSpan={5}></td>
                            <td style={{ textAlign: 'right' }}>{t('cpq.total')}</td>
                            <td style={{ textAlign: 'right' }}>{formatNumber(quote.final_amount || 0)}</td>
                        </tr>
                    </tfoot>
                </table>
            </div>
        </div>
    );
};

export default QuoteDetail;
