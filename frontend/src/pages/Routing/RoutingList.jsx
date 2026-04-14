import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { routingAPI } from '../../utils/api';
import { Plus, Edit2, Eye } from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';

const RoutingList = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const navigate = useNavigate();
    const [routings, setRoutings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('');

    useEffect(() => {
        routingAPI.list()
            .then(res => setRoutings(res.data || []))
            .catch(e => console.error(e))
            .finally(() => setLoading(false));
    }, []);

    const filtered = routings.filter(r =>
        !filter || r.name?.toLowerCase().includes(filter.toLowerCase()) ||
        r.product_name?.toLowerCase().includes(filter.toLowerCase())
    );

    return (
        <div className="module-container" dir={isRTL ? 'rtl' : 'ltr'}>
            <BackButton />
            <div className="module-header">
                <h1>{t('routing.routings')}</h1>
                <div style={{ display: 'flex', gap: 8 }}>
                    <input
                        type="text"
                        className="form-control"
                        placeholder={t('common.search')}
                        value={filter}
                        onChange={e => setFilter(e.target.value)}
                        style={{ maxWidth: 250 }}
                    />
                    <button className="btn btn-primary" onClick={() => navigate('/manufacturing/routing/new')}>
                        <Plus size={16} /> {t('routing.new_routing')}
                    </button>
                </div>
            </div>

            {loading ? (
                <div className="loading-spinner">{t('common.loading')}</div>
            ) : filtered.length === 0 ? (
                <div className="empty-state">{t('routing.no_routings')}</div>
            ) : (
                <div className="data-table-wrapper">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>{t('routing.name')}</th>
                                <th>{t('routing.product')}</th>
                                <th>{t('routing.operations_count')}</th>
                                <th>{t('routing.is_default')}</th>
                                <th>{t('routing.status')}</th>
                                <th>{t('common.actions')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map(r => (
                                <tr key={r.id}>
                                    <td><strong>{r.name}</strong></td>
                                    <td>{r.product_name || '-'}</td>
                                    <td>{(r.operations || []).length}</td>
                                    <td>
                                        {r.is_default && (
                                            <span style={{
                                                padding: '2px 8px', borderRadius: 12,
                                                background: '#dbeafe', color: '#2563eb',
                                                fontSize: 11, fontWeight: 600,
                                            }}>
                                                {t('routing.default')}
                                            </span>
                                        )}
                                    </td>
                                    <td>
                                        <span style={{
                                            padding: '2px 8px', borderRadius: 12,
                                            background: r.is_active ? '#dcfce7' : '#fee2e2',
                                            color: r.is_active ? '#16a34a' : '#dc2626',
                                            fontSize: 11, fontWeight: 600,
                                        }}>
                                            {r.is_active ? t('common.active') : t('common.inactive')}
                                        </span>
                                    </td>
                                    <td style={{ display: 'flex', gap: 4 }}>
                                        <button className="btn btn-sm btn-outline"
                                            onClick={() => navigate(`/manufacturing/routing/${r.id}`)}>
                                            <Eye size={14} />
                                        </button>
                                        <button className="btn btn-sm btn-primary"
                                            onClick={() => navigate(`/manufacturing/routing/${r.id}/edit`)}>
                                            <Edit2 size={14} />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

export default RoutingList;
