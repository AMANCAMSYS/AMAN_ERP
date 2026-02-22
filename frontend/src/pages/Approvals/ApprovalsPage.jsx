import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Plus, Check, X, RotateCcw, Eye, Settings, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import api from '../../utils/api';
import { useToast } from '../../context/ToastContext';
import { formatNumber } from '../../utils/format';
import { getCurrency, hasPermission } from '../../utils/auth';
import SimpleModal from '../../components/common/SimpleModal';
import { formatDate, formatDateTime } from '../../utils/dateUtils';

const ApprovalsPage = () => {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    const { showToast } = useToast();
    const currency = getCurrency();
    const isRTL = i18n.language === 'ar';
    const [activeTab, setActiveTab] = useState('pending'); // pending, requests, workflows

    // Permissions
    const canAction = hasPermission('approvals.action');
    const canCreate = hasPermission('approvals.create');
    const canEdit = hasPermission('approvals.edit');
    const canDelete = hasPermission('approvals.delete');

    // State
    const [pendingItems, setPendingItems] = useState([]);
    const [allRequests, setAllRequests] = useState([]);
    const [workflows, setWorkflows] = useState([]);
    const [loading, setLoading] = useState(false);

    // Action Modal State
    const [selectedRequest, setSelectedRequest] = useState(null);
    const [actionType, setActionType] = useState(null); // approve, reject, return
    const [actionNotes, setActionNotes] = useState('');
    const [submittingAction, setSubmittingAction] = useState(false);

    useEffect(() => {
        fetchData();
    }, [activeTab]);

    const fetchData = async () => {
        setLoading(true);
        try {
            if (activeTab === 'pending') {
                const response = await api.get('/approvals/pending');
                setPendingItems(response.data.items || []);
            } else if (activeTab === 'requests') {
                const response = await api.get('/approvals/requests');
                setAllRequests(response.data.items || []);
            } else if (activeTab === 'workflows') {
                const response = await api.get('/approvals/workflows');
                setWorkflows(response.data || []);
            }
        } catch (error) {
            console.error("Failed to fetch data", error);
            showToast(t('common.error_loading_data'), 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleAction = async () => {
        if (!selectedRequest || !actionType) return;

        setSubmittingAction(true);
        try {
            await api.post(`/approvals/requests/${selectedRequest.id}/action`, {
                action: actionType,
                notes: actionNotes
            });

            showToast(t('common.success_update'), 'success');
            setSelectedRequest(null);
            setActionType(null);
            setActionNotes('');
            fetchData(); // Refresh list
        } catch (error) {
            showToast(error.response?.data?.detail || t('common.error_occurred'), 'error');
        } finally {
            setSubmittingAction(false);
        }
    };

    const openActionModal = (request, type) => {
        setSelectedRequest(request);
        setActionType(type);
        setActionNotes('');
    };

    const handleDeleteWorkflow = async (id) => {
        if (!window.confirm(t('common.confirm_delete'))) return;

        try {
            await api.delete(`/approvals/workflows/${id}`);
            showToast(t('common.success_delete'), 'success');
            fetchData();
        } catch (error) {
            showToast(error.response?.data?.detail || t('common.error_deleting'), 'error');
        }
    };

    const getStatusBadge = (status) => {
        switch (status) {
            case 'pending': return <span className="badge badge-warning gap-1"><Clock size={12} /> {t('approvals.status.pending')}</span>;
            case 'approved': return <span className="badge badge-success gap-1"><CheckCircle size={12} /> {t('approvals.status.approved')}</span>;
            case 'rejected': return <span className="badge badge-error gap-1"><XCircle size={12} /> {t('approvals.status.rejected')}</span>;
            case 'returned': return <span className="badge badge-info gap-1"><RotateCcw size={12} /> {t('approvals.status.returned')}</span>;
            default: return <span className="badge badge-ghost">{status}</span>;
        }
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <h1 className="workspace-title">{t('approvals.title')}</h1>
                        <p className="workspace-subtitle">
                            {activeTab === 'pending' ? t('approvals.pending_actions') :
                                activeTab === 'requests' ? t('approvals.all_requests') :
                                    t('approvals.workflows')}
                        </p>
                    </div>
                    {activeTab === 'workflows' && canCreate && (
                        <button
                            onClick={() => navigate('/approvals/new')}
                            className="btn btn-primary shadow-lg"
                        >
                            <Plus size={20} />
                            {t('approvals.create_workflow')}
                        </button>
                    )}
                </div>
            </div>

            {/* Tabs */}
            <div className="card p-1 mb-6" style={{ width: 'fit-content', borderRadius: '12px' }}>
                <div className="tabs tabs-boxed bg-transparent">
                    <button
                        className={`tab tab-md px-6 ${activeTab === 'pending' ? 'tab-active bg-primary text-white' : ''}`}
                        onClick={() => setActiveTab('pending')}
                    >
                        {t('approvals.pending_actions')}
                        {pendingItems.length > 0 && <span className="badge badge-sm ml-2 bg-white text-primary border-none font-bold">{pendingItems.length}</span>}
                    </button>
                    <button
                        className={`tab tab-md px-6 ${activeTab === 'requests' ? 'tab-active bg-primary text-white' : ''}`}
                        onClick={() => setActiveTab('requests')}
                    >
                        {t('approvals.all_requests')}
                    </button>
                    <button
                        className={`tab tab-md px-6 ${activeTab === 'workflows' ? 'tab-active bg-primary text-white' : ''}`}
                        onClick={() => setActiveTab('workflows')}
                    >
                        {t('approvals.workflows')}
                    </button>
                </div>
            </div>

            {/* Content Container */}
            <div className="data-table-container">
                {loading ? (
                    <div className="flex justify-center items-center py-20">
                        <span className="loading loading-spinner loading-lg text-primary"></span>
                    </div>
                ) : (
                    <>
                        {/* Tab 1: Pending Actions */}
                        {activeTab === 'pending' && (
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th style={{ width: '80px' }}>{t('approvals.table.id')}</th>
                                        <th>{t('approvals.table.document')}</th>
                                        <th>{t('approvals.table.requested_by')}</th>
                                        <th>{t('approvals.table.date')}</th>
                                        <th>{t('approvals.table.current_step')}</th>
                                        {canAction && <th style={{ width: '150px' }}>{t('approvals.table.actions')}</th>}
                                    </tr>
                                </thead>
                                <tbody>
                                    {pendingItems.length === 0 ? (
                                        <tr><td colSpan={canAction ? 6 : 5} className="text-center py-12 opacity-50">{t('approvals.table.no_pending')}</td></tr>
                                    ) : (
                                        pendingItems.map((item) => (
                                            <tr key={item.id}>
                                                <td className="font-mono text-sm text-primary font-medium">#{item.id}</td>
                                                <td>
                                                    <div className="font-bold">{t(`approvals.document_types.${item.document_type}`) || item.document_type}</div>
                                                    <div className="text-xs opacity-70">{t('approvals.table.ref')}: {item.document_id} • <strong>{formatNumber(item.amount)} {currency}</strong></div>
                                                    {item.description && <div className="text-xs italic mt-1 text-base-content/60 max-w-xs truncate">{item.description}</div>}
                                                </td>
                                                <td>{item.requested_by_name || '—'}</td>
                                                <td>{formatDate(item.created_at)}</td>
                                                <td>
                                                    <div className="badge badge-outline badge-sm">{t('approvals.table.step')} {item.current_step} / {item.total_steps}</div>
                                                </td>
                                                {canAction && (
                                                    <td>
                                                        <div className="flex gap-1">
                                                            <button
                                                                onClick={() => openActionModal(item, 'approve')}
                                                                className="btn btn-xs btn-success text-white"
                                                                title={t('common.approve')}
                                                            >
                                                                <Check size={14} />
                                                            </button>
                                                            <button
                                                                onClick={() => openActionModal(item, 'return')}
                                                                className="btn btn-xs btn-warning text-white"
                                                                title={t('approvals.actions.return')}
                                                            >
                                                                <RotateCcw size={14} />
                                                            </button>
                                                            <button
                                                                onClick={() => openActionModal(item, 'reject')}
                                                                className="btn btn-xs btn-error text-white"
                                                                title={t('common.reject')}
                                                            >
                                                                <X size={14} />
                                                            </button>
                                                        </div>
                                                    </td>
                                                )}
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        )}

                        {/* Tab 2: All Requests */}
                        {activeTab === 'requests' && (
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th style={{ width: '80px' }}>{t('approvals.table.id')}</th>
                                        <th>{t('approvals.table.workflow')}</th>
                                        <th>{t('approvals.table.document')}</th>
                                        <th>{t('approvals.table.requested_by')}</th>
                                        <th>{t('approvals.table.date')}</th>
                                        <th>{t('approvals.table.status')}</th>
                                        <th style={{ width: '50px' }}></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {allRequests.length === 0 ? (
                                        <tr><td colSpan="7" className="text-center py-12 opacity-50">{t('approvals.table.no_requests')}</td></tr>
                                    ) : (
                                        allRequests.map((item) => (
                                            <tr key={item.id}>
                                                <td className="font-mono text-sm text-primary font-medium">#{item.id}</td>
                                                <td><span className="font-medium">{item.workflow_name}</span></td>
                                                <td>
                                                    <div className="font-bold">{t(`approvals.document_types.${item.document_type}`) || item.document_type}</div>
                                                    <div className="text-xs opacity-70">{t('approvals.table.ref')}: {item.document_id} • <strong>{formatNumber(item.amount)} {currency}</strong></div>
                                                </td>
                                                <td>{item.requested_by_name || '—'}</td>
                                                <td>{formatDate(item.created_at)}</td>
                                                <td>{getStatusBadge(item.status)}</td>
                                                <td>
                                                    <button className="btn btn-ghost btn-xs text-primary" title={t('common.view_details')}>
                                                        <Eye size={16} />
                                                    </button>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        )}

                        {/* Tab 3: Workflows */}
                        {activeTab === 'workflows' && (
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>{t('approvals.table.name')}</th>
                                        <th>{t('approvals.table.document_type')}</th>
                                        <th>{t('approvals.table.steps')}</th>
                                        <th>{t('approvals.table.active')}</th>
                                        <th style={{ width: '100px' }}>{t('approvals.table.actions')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {workflows.length === 0 ? (
                                        <tr><td colSpan="5" className="text-center py-12 opacity-50">{t('approvals.table.no_workflows')}</td></tr>
                                    ) : (
                                        workflows.map((wf) => (
                                            <tr key={wf.id}>
                                                <td className="font-bold">{wf.name}</td>
                                                <td>{t(`approvals.document_types.${wf.document_type}`) || wf.document_type}</td>
                                                <td>
                                                    {(() => {
                                                        try {
                                                            const steps = typeof wf.steps === 'string' ? JSON.parse(wf.steps) : wf.steps;
                                                            return <span className="badge badge-secondary badge-outline badge-sm">{steps?.length || 0} {t('approvals.table.steps')}</span>;
                                                        } catch (e) {
                                                            return <span className="badge badge-ghost badge-sm">Invalid Data</span>;
                                                        }
                                                    })()}
                                                </td>
                                                <td>
                                                    {wf.is_active ?
                                                        <span className="badge badge-success badge-sm">{t('common.active')}</span> :
                                                        <span className="badge badge-ghost badge-sm">{t('common.inactive')}</span>
                                                    }
                                                </td>
                                                <td>
                                                    <div className="flex gap-1">
                                                        {canEdit && (
                                                            <button
                                                                onClick={() => navigate(`/approvals/${wf.id}/edit`)}
                                                                className="btn btn-ghost btn-xs text-primary"
                                                                title={t('common.edit')}
                                                            >
                                                                <Settings size={16} />
                                                            </button>
                                                        )}
                                                        {canDelete && (
                                                            <button
                                                                onClick={() => handleDeleteWorkflow(wf.id)}
                                                                className="btn btn-ghost btn-xs text-error"
                                                                title={t('common.delete')}
                                                            >
                                                                <X size={16} />
                                                            </button>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        )}
                    </>
                )}
            </div>

            {/* Action Modal */}
            <SimpleModal
                isOpen={!!selectedRequest}
                onClose={() => setSelectedRequest(null)}
                title={
                    actionType === 'approve' ? t('common.approve') :
                        actionType === 'reject' ? t('common.reject') :
                            actionType === 'return' ? t('approvals.actions.return') : t('common.view_details')
                }
            >
                <div className="p-4 space-y-4">
                    <div className="alert alert-info bg-primary/5 border-primary/20 text-sm">
                        <AlertCircle size={18} className="text-primary" />
                        <div>
                            {t('approvals.approvals.confirm_action_on_this_request')}
                        </div>
                    </div>

                    {selectedRequest && (
                        <div className="bg-base-200/50 p-4 rounded-xl border border-base-200">
                            <div className="flex justify-between items-start mb-2">
                                <div className="font-bold text-lg">{t(`approvals.document_types.${selectedRequest.document_type}`) || selectedRequest.document_type}</div>
                                <div className="font-mono text-primary">#{selectedRequest.document_id}</div>
                            </div>
                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <span className="opacity-60 block">{t('common.amount')}</span>
                                    <span className="font-bold">{formatNumber(selectedRequest.amount)} {currency}</span>
                                </div>
                                <div>
                                    <span className="opacity-60 block">{t('approvals.table.requested_by')}</span>
                                    <span>{selectedRequest.requested_by_name}</span>
                                </div>
                                {selectedRequest.description && (
                                    <div className="col-span-2 mt-2">
                                        <span className="opacity-60 block">{t('common.description')}</span>
                                        <div className="italic text-base-content/70">{selectedRequest.description}</div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    <div className="form-input">
                        <label className="label">
                            <span className="label-text font-medium">{t('common.notes')}</span>
                        </label>
                        <textarea
                            className="textarea textarea-bordered h-24 focus:border-primary"
                            placeholder={isRTL ? "أضف ملاحظاتك هنا (اختياري)..." : "Add notes here (optional)..."}
                            value={actionNotes}
                            onChange={(e) => setActionNotes(e.target.value)}
                        />
                    </div>

                    <div className="flex justify-end gap-3 pt-4 border-t border-base-200">
                        <button
                            className="btn btn-ghost"
                            onClick={() => setSelectedRequest(null)}
                            disabled={submittingAction}
                        >
                            {t('common.cancel')}
                        </button>
                        <button
                            className={`btn ${actionType === 'approve' ? 'btn-success' :
                                actionType === 'reject' ? 'btn-error' : 'btn-warning'
                                } text-white min-w-[120px]`}
                            onClick={handleAction}
                            disabled={submittingAction}
                        >
                            {submittingAction ?
                                <span className="loading loading-spinner loading-sm"></span> :
                                (actionType === 'approve' ? t('common.approve') :
                                    actionType === 'reject' ? t('common.reject') :
                                        t('approvals.actions.return'))
                            }
                        </button>
                    </div>
                </div>
            </SimpleModal>
        </div>
    );
};

export default ApprovalsPage;
