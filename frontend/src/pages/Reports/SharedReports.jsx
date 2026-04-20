import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { reportSharingAPI } from '../../services/reports';
import { useToast } from '../../context/ToastContext';
import { formatDate } from '../../utils/dateUtils';
import BackButton from '../../components/common/BackButton';

const SharedReports = () => {
    const { t } = useTranslation();
    const { showToast } = useToast();
    const navigate = useNavigate();
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchShared();
    }, []);

    const fetchShared = async () => {
        try {
            setLoading(true);
            const res = await reportSharingAPI.listShared();
            setReports(res.data);
        } catch (err) {
            console.error(err);
            showToast(t('common.error_loading'), 'error');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">🔗 {t('reports.sharing.shared_with_me', 'Shared With Me')}</h1>
                    <p className="workspace-subtitle">
                        {t('reports.sharing.shared_subtitle', 'Reports that colleagues have shared with you')}
                    </p>
                </div>
            </div>

            <div className="table-container">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>{t('reports.report_name', 'Report Name')}</th>
                            <th>{t('reports.sharing.shared_by', 'Shared By')}</th>
                            <th>{t('reports.sharing.permission_label', 'Permission')}</th>
                            <th>{t('reports.sharing.message', 'Message')}</th>
                            <th>{t('reports.sharing.shared_on', 'Shared On')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan="5" className="text-center">{t('common.loading')}</td></tr>
                        ) : reports.length === 0 ? (
                            <tr><td colSpan="5" className="text-center">{t('reports.sharing.no_shared')}</td></tr>
                        ) : (
                            reports.map(r => (
                                <tr key={r.id}>
                                    <td style={{ fontWeight: 600 }}>
                                        <span
                                            className="text-primary"
                                            style={{ cursor: 'pointer', textDecoration: 'underline' }}
                                            onClick={() => navigate(`/reports/${r.report_type}/${r.report_id}`)}
                                        >
                                            {r.report_name || `${r.report_type} #${r.report_id}`}
                                        </span>
                                    </td>
                                    <td>{r.shared_by_name}</td>
                                    <td>
                                        <span className={`badge ${r.permission === 'edit' ? 'badge-warning' : 'badge-secondary'}`}>
                                            {t(`reports.sharing.${r.permission}`, r.permission)}
                                        </span>
                                    </td>
                                    <td>{r.message || '-'}</td>
                                    <td>{formatDate(r.created_at)}</td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default SharedReports;
