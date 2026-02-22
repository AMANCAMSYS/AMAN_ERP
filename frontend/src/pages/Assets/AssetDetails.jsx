import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { assetsAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import { Trash2, Calendar, DollarSign, Activity, FileText } from 'lucide-react';
import { getCurrency } from '../../utils/auth';
import { formatShortDate } from '../../utils/dateUtils';
import BackButton from '../../components/common/BackButton';

const AssetDetails = () => {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    const { id } = useParams();
    const isRTL = i18n.language === 'ar';
    const currency = getCurrency();

    const [asset, setAsset] = useState(null);
    const [schedule, setSchedule] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
    }, [id]);

    const fetchData = async () => {
        try {
            setLoading(true);
            const response = await assetsAPI.get(id);
            setAsset(response.data.asset);
            setSchedule(response.data.schedule);
        } catch (error) {
            console.error("Failed to fetch asset details", error);
            navigate('/assets');
        } finally {
            setLoading(false);
        }
    };

    const handlePostDepreciation = async (scheduleId) => {
        if (!window.confirm(t('assets.confirm_post', 'Are you sure you want to post depreciation for this period?'))) return;

        try {
            await assetsAPI.postDepreciation(id, scheduleId);
            toastEmitter.emit(t('assets.depr_posted', 'Depreciation posted successfully'), 'success');
            fetchData();
        } catch (error) {
            console.error("Failed to post depreciation", error);
        }
    };

    const handleDispose = async () => {
        if (!window.confirm(t('assets.confirm_dispose'))) return;
        try {
            await assetsAPI.dispose(id, { disposal_date: new Date().toISOString().split('T')[0] });
            toastEmitter.emit(t('assets.disposed_msg'), 'success');
            fetchData();
        } catch (error) {
            console.error("Failed to dispose asset", error);
            toastEmitter.emit(t('common.error_occurred'), 'error');
        }
    };

    if (loading) return <div className="text-center py-5"><span className="loading"></span></div>;
    if (!asset) return null;

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div className="d-flex align-items-center justify-content-between w-100">
                    <div className="d-flex align-items-center gap-3">
                        <BackButton />
                        <div>
                            <h1 className="workspace-title text-primary">{asset.name}</h1>
                            <p className="workspace-subtitle text-muted fw-medium">
                                <span className="badge bg-light text-dark border me-2">{asset.code}</span>
                                <span className="text-secondary">{t(`assets.types.${asset.type}`, asset.type)}</span>
                            </p>
                        </div>
                    </div>
                    <div className="header-actions">
                        {asset.status === 'active' && (
                            <button className="btn btn-sm btn-outline-danger me-2" onClick={handleDispose}>
                                <Trash2 size={16} className="me-1" />
                                {t('assets.dispose')}
                            </button>
                        )}
                        <span className={`badge ${asset.status === 'active' ? 'bg-success-subtle text-success' : 'bg-secondary-subtle text-secondary'} border px-3 py-2 fs-6`}>
                            {t(`status.${asset.status}`, asset.status)}
                        </span>
                    </div>
                </div>
            </div>

            <div className="row g-4">
                {/* Asset Info Card */}
                <div className="col-md-4">
                    <div className="card section-card h-100">
                        <h3 className="section-title mb-4">{t('assets.details', 'Asset Details')}</h3>

                        <div className="detail-row mb-3">
                            <label className="text-muted d-block small mb-1">{t('assets.purchase_date', 'Purchase Date')}</label>
                            <div className="fw-medium d-flex align-items-center">
                                <Calendar size={16} className="me-2 text-primary" />
                                {formatShortDate(asset.purchase_date)}
                            </div>
                        </div>

                        <div className="detail-row mb-3">
                            <label className="text-muted d-block small mb-1">{t('assets.cost', 'Initial Cost')}</label>
                            <div className="fw-bold fs-5 text-dark d-flex align-items-center">
                                <DollarSign size={18} className="me-2 text-success" />
                                {parseFloat(asset.cost).toLocaleString()} <span className="text-muted fs-6 ms-1">{currency}</span>
                            </div>
                        </div>

                        <div className="detail-row mb-3">
                            <label className="text-muted d-block small mb-1">{t('assets.residual_value', 'Residual Value')}</label>
                            <div className="fw-medium">
                                {parseFloat(asset.residual_value).toLocaleString()} {currency}
                            </div>
                        </div>

                        <div className="detail-row mb-3">
                            <label className="text-muted d-block small mb-1">{t('assets.life_years', 'Useful Life')}</label>
                            <div className="fw-medium">
                                {asset.life_years} {t('common.years', 'Years')}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Depreciation Schedule */}
                <div className="col-md-8">
                    <div className="card section-card h-100">
                        <h3 className="section-title mb-4">{t('assets.depr_schedule', 'Depreciation Schedule')}</h3>
                        <div className="data-table-container">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>{t('common.year', 'Year')}</th>
                                        <th className="text-end">{t('assets.amount', 'Expense Amount')}</th>
                                        <th className="text-end">{t('assets.accumulated', 'Accumulated')}</th>
                                        <th className="text-end">{t('assets.book_value', 'Book Value')}</th>
                                        <th className="text-center">{t('common.status.title', 'Status')}</th>
                                        <th className="text-center">{t('common.actions', 'Actions')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {schedule.map((item, index) => (
                                        <tr key={item.id}>
                                            <td className="fw-medium">{item.fiscal_year}</td>
                                            <td className="text-end">{parseFloat(item.amount).toLocaleString()}</td>
                                            <td className="text-end text-muted">{parseFloat(item.accumulated_amount).toLocaleString()}</td>
                                            <td className="text-end fw-bold text-primary">{parseFloat(item.book_value).toLocaleString()}</td>
                                            <td className="text-center">
                                                {item.posted ? (
                                                    <span className="badge bg-success-subtle text-success">{t('status.posted', 'Posted')}</span>
                                                ) : (
                                                    <span className="badge bg-warning-subtle text-warning">{t('status.pending', 'Pending')}</span>
                                                )}
                                            </td>
                                            <td className="text-center">
                                                {!item.posted && (
                                                    <button
                                                        className="btn btn-sm btn-outline-primary"
                                                        onClick={() => handlePostDepreciation(item.id)}
                                                    >
                                                        {t('assets.post_entry', 'Post Entry')}
                                                    </button>
                                                )}
                                                {item.posted && item.journal_entry_id && (
                                                    <small className="text-muted">JE #{item.journal_entry_id}</small>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                    {schedule.length === 0 && (
                                        <tr><td colSpan="6" className="text-center py-4 text-muted">{t('common.no_data')}</td></tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AssetDetails;
