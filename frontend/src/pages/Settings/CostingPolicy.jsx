
import React, { useState, useEffect } from 'react'; // Re-triggering Vite rebuild after backend fix
import {
    Check,
    Activity,
    Database,
    BarChart3,
    BrainCircuit,
    Globe,
    Store,
    Scale,
    Info,
    History as HistoryIcon
} from 'lucide-react';
import api from '../../utils/api';
import { costingPolicyAPI, branchesAPI } from '../../utils/api';
import { useTranslation } from 'react-i18next';
import { useToast } from '../../context/ToastContext';
import BackButton from '../../components/common/BackButton';
import { PageLoading } from '../../components/common/LoadingStates'

const CostingPolicy = () => {
    const { t } = useTranslation();
    const { showToast } = useToast();
    const [currentPolicy, setCurrentPolicy] = useState(null);
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [processing, setProcessing] = useState(false);

    const [recommendation, setRecommendation] = useState({
        type: 'global_wac',
        reason: t('settings.costing.analyzing'),
        score: 0
    });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [policyRes, historyRes, branchesRes] = await Promise.all([
                costingPolicyAPI.getCurrent(),
                costingPolicyAPI.getHistory(),
                branchesAPI.list()
            ]);
            setCurrentPolicy(policyRes.data);
            setHistory(historyRes.data);

            const branchCount = branchesRes.data.length;
            let rec = { type: 'global_wac', reason: '', score: 90 };

            if (branchCount <= 1) {
                rec = {
                    type: 'global_wac',
                    reason: t('settings.costing.rec_single'),
                    score: 98
                };
            } else if (branchCount <= 3) {
                rec = {
                    type: 'per_warehouse_wac',
                    reason: t('settings.costing.rec_few'),
                    score: 95
                };
            } else {
                rec = {
                    type: 'hybrid',
                    reason: t('settings.costing.rec_many'),
                    score: 92
                };
            }
            setRecommendation(rec);

        } catch (error) {
            console.error("Failed to fetch policy data", error);
            showToast(t('settings.costing.error_load'), 'error');
        } finally {
            setLoading(false);
        }
    };


    const [confirmingType, setConfirmingType] = useState(null);

    const handleSetPolicy = async (type) => {
        if (confirmingType !== type) {
            setConfirmingType(type);
            return;
        }

        try {
            setProcessing(true);
            await costingPolicyAPI.setPolicy({
                policy_type: type,
                reason: "Changed via Settings UI"
            });
            setConfirmingType(null);
            await fetchData();
            showToast(t('settings.costing.success_update'), 'success');
        } catch (error) {
            console.error("Error setting policy", error);
            showToast(t('settings.costing.error_update'), 'error');
        } finally {
            setProcessing(false);
        }
    };

    const policies = [
        {
            id: 'global_wac',
            name: t('settings.costing.global_wac'),
            icon: Globe,
            desc: t('settings.costing.global_wac_desc'),
            pros: [t('settings.costing.pro_simple'), t('settings.costing.pro_easy'), t('settings.costing.pro_fast')],
            cons: [t('settings.costing.con_less_accurate'), t('settings.costing.con_no_transport')],
            colorClass: 'bg-primary-subtle',
            iconColor: 'var(--primary)'
        },
        {
            id: 'per_warehouse_wac',
            name: t('settings.costing.per_warehouse'),
            icon: Store,
            desc: t('settings.costing.per_warehouse_desc'),
            pros: [t('settings.costing.pro_high_accuracy'), t('settings.costing.pro_real_profit'), t('settings.costing.pro_precise_tracking')],
            cons: [t('settings.costing.con_complex'), t('settings.costing.con_precise_mgmt')],
            colorClass: 'bg-success-subtle',
            iconColor: 'var(--success)'
        },
        {
            id: 'hybrid',
            name: t('settings.costing.hybrid'),
            icon: Scale,
            desc: t('settings.costing.hybrid_desc'),
            pros: [t('settings.costing.pro_balanced'), t('settings.costing.pro_flexible')],
            cons: [t('settings.costing.con_needs_classification')],
            colorClass: 'bg-secondary-subtle',
            iconColor: 'var(--secondary)'
        },
        {
            id: 'smart',
            name: t('settings.costing.smart'),
            icon: BrainCircuit,
            desc: t('settings.costing.smart_desc'),
            pros: [t('settings.costing.pro_full_automation'), t('settings.costing.pro_continuous_improvement'), t('settings.costing.pro_ml')],
            cons: [t('settings.costing.con_advanced'), t('settings.costing.con_needs_history')],
            colorClass: 'bg-warning-subtle',
            iconColor: 'var(--warning)',
            isComingSoon: true
        }
    ];

    if (loading) return <PageLoading />;

    return (
        <div className="workspace fade-in" dir="rtl">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title flex items-center gap-2">
                        <Database className="w-8 h-8 text-primary" style={{ color: 'var(--primary)' }} />
                        {t('settings.costing.title')}
                    </h1>
                    <p className="workspace-subtitle">{t('settings.costing.subtitle')}</p>
                </div>
                <div className="header-actions">
                    <div className={`badge ${currentPolicy?.is_active ? 'badge-success' : 'badge-secondary'}`} style={{ fontSize: '16px', padding: '8px 16px' }}>
                        {t('settings.costing.current_policy')}: {currentPolicy?.policy_name || t('settings.costing.not_set')}
                    </div>
                </div>
            </div>

            {/* Recommendation Banner */}
            <div className="alert bg-primary-subtle" style={{ display: 'flex', alignItems: 'center', gap: '12px', border: '1px solid var(--primary-light)', color: 'var(--primary)', marginBottom: '32px' }}>
                <Info size={20} />
                <div>
                    <span style={{ fontWeight: '700' }}>{t('settings.costing.recommendation')} </span>
                    {policies.find(p => p.id === recommendation.type)?.name}.
                    {recommendation.reason}
                </div>
            </div>

            {/* Policy Selection Grid */}
            <div className="modules-grid" style={{ marginBottom: '40px' }}>
                {policies.map((policy) => {
                    const isActive = currentPolicy?.policy_type === policy.id;
                    const Icon = policy.icon;

                    return (
                        <div
                            key={policy.id}
                            className="card"
                            style={{
                                padding: '24px',
                                position: 'relative',
                                border: isActive ? '2px solid var(--primary)' : '1px solid var(--border-color)',
                                backgroundColor: policy.colorClass ? 'rgba(var(--primary-rgb), 0.02)' : 'white',
                                boxShadow: isActive ? 'var(--shadow-lg)' : 'var(--shadow-sm)'
                            }}
                        >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
                                <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                                    <div style={{
                                        width: '48px',
                                        height: '48px',
                                        borderRadius: '12px',
                                        backgroundColor: 'white',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        boxShadow: 'var(--shadow-sm)',
                                        color: policy.iconColor
                                    }}>
                                        <Icon size={28} />
                                    </div>
                                    <div>
                                        <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '700' }}>{policy.name}</h3>
                                        <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-secondary)' }}>{policy.desc}</p>
                                    </div>
                                </div>
                                {isActive && <span className="badge badge-success">{t('settings.costing.active_now')}</span>}
                                {policy.isComingSoon && <span className="badge badge-warning">{t('settings.costing.coming_soon')}</span>}
                            </div>

                            <div className="policy-details" style={{ marginTop: '20px' }}>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', fontSize: '13px' }}>
                                    <div>
                                        <div style={{ fontWeight: '700', color: 'var(--success)', marginBottom: '8px' }}>{t('settings.costing.advantages')}</div>
                                        <ul style={{ paddingRight: '16px', margin: 0, color: 'var(--text-secondary)' }}>
                                            {policy.pros.map((p, i) => <li key={i} style={{ marginBottom: '4px' }}>{p}</li>)}
                                        </ul>
                                    </div>
                                    <div>
                                        <div style={{ fontWeight: '700', color: 'var(--danger)', marginBottom: '8px' }}>{t('settings.costing.challenges')}</div>
                                        <ul style={{ paddingRight: '16px', margin: 0, color: 'var(--text-secondary)' }}>
                                            {policy.cons.map((c, i) => <li key={i} style={{ marginBottom: '4px' }}>{c}</li>)}
                                        </ul>
                                    </div>
                                </div>


                                <button
                                    onClick={() => !policy.isComingSoon && handleSetPolicy(policy.id)}
                                    disabled={(isActive && confirmingType !== policy.id) || processing || policy.isComingSoon}
                                    className={`btn ${isActive ? 'btn-secondary' : (policy.isComingSoon ? 'btn-outline-secondary' : (confirmingType === policy.id ? 'btn-danger' : 'btn-primary'))} btn-block`}
                                    style={{
                                        marginTop: '24px',
                                        transform: confirmingType === policy.id ? 'scale(1.02)' : 'scale(1)',
                                        transition: 'all 0.2s ease',
                                        cursor: policy.isComingSoon ? 'not-allowed' : 'pointer'
                                    }}
                                >
                                    {policy.isComingSoon ? t('settings.costing.very_soon') :
                                        (isActive ? t('settings.costing.applied') :
                                            confirmingType === policy.id ? t('settings.costing.confirm_activate') : t('settings.costing.activate'))}
                                </button>
                                {confirmingType === policy.id && (
                                    <button
                                        className="btn btn-link btn-block"
                                        onClick={() => setConfirmingType(null)}
                                        style={{ fontSize: '12px', color: 'var(--text-muted)' }}
                                    >
                                        {t('common.cancel')}
                                    </button>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* History Section */}
            <div className="section-card" style={{ padding: '30px' }}>
                <div className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '18px', color: 'var(--text-primary)' }}>
                    <HistoryIcon size={20} />
                    {t('settings.costing.change_history')}
                </div>

                <div className="data-table-container mt-4">
                    <table className="data-table">

                        <thead>
                            <tr>
                                <th style={{ width: '15%' }}>{t('settings.costing.from_policy')}</th>
                                <th style={{ width: '15%' }}>{t('settings.costing.to_policy')}</th>
                                <th style={{ width: '18%' }}>{t('settings.costing.date')}</th>
                                <th style={{ width: '12%' }}>{t('settings.costing.by_user')}</th>
                                <th style={{ width: '40%' }}>{t('settings.costing.details_impact')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {history.map((h, i) => (
                                <tr key={i}>
                                    <td>
                                        <span className="badge" style={{ backgroundColor: 'var(--bg-hover)', color: 'var(--text-secondary)' }}>
                                            {h.old_policy_type || '-'}
                                        </span>
                                    </td>
                                    <td>
                                        <span className="badge badge-primary" style={{ backgroundColor: 'var(--primary-subtle)', color: 'var(--primary)' }}>
                                            {h.new_policy_type}
                                        </span>
                                    </td>
                                    <td style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                                        {new Date(h.change_date).toLocaleString('ar-SA')}
                                    </td>
                                    <td style={{ fontWeight: '500' }}>{h.changed_by_name || 'System'}</td>
                                    <td>
                                        <div style={{ fontSize: '13px', fontWeight: '500', marginBottom: '4px' }}>{h.reason || '-'}</div>
                                        {h.affected_products_count > 0 && (
                                            <div className="flex items-center gap-2" style={{ fontSize: '11px', color: 'var(--primary)', backgroundColor: 'var(--primary-subtle)', padding: '4px 8px', borderRadius: '4px', display: 'inline-flex' }}>
                                                <Activity size={12} />
                                                <span>{t('settings.costing.products_updated')} <b>{h.affected_products_count}</b> {t('settings.costing.product')}</span>
                                                {h.total_cost_impact > 0 && <span> | {t('settings.costing.cost_impact')}: <b>{h.total_cost_impact.toLocaleString()}</b></span>}
                                                <span style={{ marginLeft: '4px' }} className="badge badge-success">{t('settings.costing.completed')}</span>
                                            </div>
                                        )}
                                        {!h.affected_products_count && (
                                            <span className="badge badge-secondary" style={{ fontSize: '10px' }}>{t('settings.costing.settings_change')}</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                            {history.length === 0 && (
                                <tr>
                                    <td colSpan="5" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                                        {t('settings.costing.no_history')}
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div >
    );
};

export default CostingPolicy;
