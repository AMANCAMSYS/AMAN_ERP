import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { expensesAPI } from '../../utils/api';
import { useToast } from '../../context/ToastContext';
import { 
  ArrowLeft, Edit, Trash2, CheckCircle, XCircle, FileText, 
  DollarSign, User, Clock, Receipt 
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { formatNumber } from '../../utils/format';
import { getCurrency } from '../../utils/auth';
import SimpleModal from '../../components/common/SimpleModal';

export default function ExpenseDetails() {
  const { t, i18n } = useTranslation();
  const isRTL = i18n.language === 'ar';
  const { id } = useParams();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const currency = getCurrency() || '';

  const [expense, setExpense] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [approvalAction, setApprovalAction] = useState('');
  const [approvalNotes, setApprovalNotes] = useState('');
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    loadExpense();
  }, [id]);

  const loadExpense = async () => {
    try {
      setLoading(true);
      const res = await expensesAPI.get(id);
      setExpense(res.data);
    } catch (error) {
      showToast(t('expenses.errors.loadFailed'), 'error');
      navigate('/expenses');
    } finally {
      setLoading(false);
    }
  };

  const handleApproval = (action) => {
    setApprovalAction(action);
    setApprovalNotes('');
    setShowApprovalModal(true);
  };

  const submitApproval = async () => {
    try {
      setProcessing(true);
      await expensesAPI.approve(id, {
        approval_status: approvalAction,
        approval_notes: approvalNotes
      });
      showToast(
        approvalAction === 'approved' 
          ? t('expenses.messages.approved') 
          : t('expenses.messages.rejected'),
        'success'
      );
      setShowApprovalModal(false);
      loadExpense();
    } catch (error) {
      showToast(t('expenses.errors.approvalFailed'), 'error');
    } finally {
      setProcessing(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm(t('expenses.confirmDelete'))) return;

    try {
      await expensesAPI.delete(id);
      showToast(t('expenses.messages.deleted'), 'success');
      navigate('/expenses');
    } catch (error) {
      showToast(t('expenses.errors.deleteFailed'), 'error');
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: { bg: '#fef3c7', color: '#d97706', icon: '⏳' },
      approved: { bg: '#dcfce7', color: '#16a34a', icon: '✅' },
      rejected: { bg: '#fee2e2', color: '#dc2626', icon: '❌' }
    };
    const s = styles[status] || styles.pending;
    return (
      <span style={{ background: s.bg, color: s.color, padding: '6px 16px', borderRadius: '20px', fontSize: '14px', fontWeight: '600' }}>
        {s.icon} {t(`expenses.status.${status}`)}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="workspace fade-in">
        <div className="text-center py-5">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">{t('common.loading')}</span>
          </div>
        </div>
      </div>
    );
  }

  if (!expense) {
    return null;
  }

  return (
    <div className="workspace fade-in">
      {/* Header */}
      <div className="workspace-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <button onClick={() => navigate('/expenses')} className="table-action-btn" style={{ background: 'var(--bg-hover)', borderRadius: '50%', width: '36px', height: '36px', display: 'flex', alignItems: 'center', justifyContent: 'center', border: 'none' }}>
              <ArrowLeft size={20} />
            </button>
            <div>
              <h1 className="workspace-title">{expense.expense_number}</h1>
              <p className="text-muted small mb-0">{t('expenses.detailsSubtitle')}</p>
            </div>
          </div>
        <div className="d-flex gap-2">
          {expense.approval_status === 'pending' && (
            <>
              <button
                className="btn btn-success d-flex align-items-center gap-2"
                onClick={() => handleApproval('approved')}
              >
                <CheckCircle size={20} />
                {t('expenses.actions.approve')}
              </button>
              <button
                className="btn btn-danger d-flex align-items-center gap-2"
                onClick={() => handleApproval('rejected')}
              >
                <XCircle size={20} />
                {t('expenses.actions.reject')}
              </button>
              <button
                className="btn btn-outline-primary d-flex align-items-center gap-2"
                onClick={() => navigate(`/expenses/${id}/edit`)}
              >
                <Edit size={20} />
                {t('common.edit')}
              </button>
              <button
                className="btn btn-outline-danger d-flex align-items-center gap-2"
                onClick={handleDelete}
              >
                <Trash2 size={20} />
                {t('common.delete')}
              </button>
            </>
          )}
        </div>
        </div>
      </div>

      {/* Status Card */}
      <div className="card border-0 shadow-sm mb-4" style={{ borderRadius: '12px' }}>
        <div className="card-body p-4">
        <div className="d-flex justify-content-between align-items-center">
          <div>
            <h5 className="mb-1">{t('expenses.fields.status')}</h5>
            {getStatusBadge(expense.approval_status)}
          </div>
          <div className="text-end">
            <div className="fs-3 fw-bold text-primary">
              {formatNumber(expense.amount)} <span className="fs-6 text-muted fw-normal">{currency}</span>
            </div>
            <small className="text-muted">
              {t(`expenses.types.${expense.expense_type}`)}
            </small>
          </div>
        </div>
        </div>
      </div>

      <div className="row">
        {/* Basic Information */}
        <div className="col-md-6 mb-4">
          <div className="card border-0 shadow-sm h-100" style={{ borderRadius: '12px' }}>
            <div className="card-body p-4">
              <div className="d-flex align-items-center gap-2 mb-3">
                <div style={{ background: '#eff6ff', width: '32px', height: '32px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <FileText size={18} color="#3b82f6" />
                </div>
                <h5 className="mb-0 fw-semibold">{t('expenses.sections.basic')}</h5>
              </div>

              <div className="info-grid">
              <div className="info-item">
                <span className="info-label">{t('expenses.fields.date')}</span>
                <span className="info-value">
                  {new Date(expense.expense_date).toLocaleDateString(isRTL ? 'ar-EG' : 'en-US')}
                </span>
              </div>

              <div className="info-item">
                <span className="info-label">{t('expenses.fields.type')}</span>
                <span className="info-value">
                  <span style={{ background: '#e0f2fe', color: '#0284c7', padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: '600' }}>
                    {t(`expenses.types.${expense.expense_type}`)}
                  </span>
                </span>
              </div>

              <div className="info-item">
                <span className="info-label">{t('expenses.fields.category')}</span>
                <span className="info-value">{expense.category || '-'}</span>
              </div>

              <div className="info-item">
                <span className="info-label">{t('expenses.fields.vendor')}</span>
                <span className="info-value">{expense.vendor_name || '-'}</span>
              </div>

              <div className="info-item">
                <span className="info-label">{t('expenses.fields.receiptNumber')}</span>
                <span className="info-value">{expense.receipt_number || '-'}</span>
              </div>

              <div className="info-item">
                <span className="info-label">{t('expenses.fields.description')}</span>
                <span className="info-value">{expense.description || '-'}</span>
              </div>
              </div>
            </div>
          </div>
        </div>

        {/* Accounting Information */}
        <div className="col-md-6 mb-4">
          <div className="card border-0 shadow-sm h-100" style={{ borderRadius: '12px' }}>
            <div className="card-body p-4">
              <div className="d-flex align-items-center gap-2 mb-3">
                <div style={{ background: '#dcfce7', width: '32px', height: '32px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <DollarSign size={18} color="#16a34a" />
                </div>
                <h5 className="mb-0 fw-semibold">{t('expenses.sections.accounting')}</h5>
              </div>

            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">{t('expenses.fields.paymentMethod')}</span>
                <span className="info-value">
                  {t(`expenses.payment.${expense.payment_method}`)}
                </span>
              </div>

              <div className="info-item">
                <span className="info-label">{t('expenses.fields.treasury')}</span>
                <span className="info-value">{expense.treasury_name || '-'}</span>
              </div>

              <div className="info-item">
                <span className="info-label">{t('expenses.fields.account')}</span>
                <span className="info-value">
                  {expense.expense_account_number ? (
                    <>{expense.expense_account_number} - {expense.expense_account_name}</>
                  ) : '-'}
                </span>
              </div>

              <div className="info-item">
                <span className="info-label">{t('expenses.fields.costCenter')}</span>
                <span className="info-value">{expense.cost_center_name || '-'}</span>
              </div>

              <div className="info-item">
                <span className="info-label">{t('expenses.fields.project')}</span>
                <span className="info-value">
                  {expense.project_code ? (
                    <>{expense.project_code} - {expense.project_name}</>
                  ) : '-'}
                </span>
              </div>

              {expense.journal_entry && (
                <div className="info-item">
                  <span className="info-label">{t('expenses.fields.journalEntry')}</span>
                  <span className="info-value">
                    <a href={`/accounting/journal-entries/${expense.journal_entry.id}`} className="text-primary">
                      {expense.journal_entry.entry_number}
                    </a>
                  </span>
                </div>
              )}
            </div>
            </div>
          </div>
        </div>

        {/* Approval Information */}
        <div className="col-md-12 mb-4">
          <div className="card border-0 shadow-sm" style={{ borderRadius: '12px' }}>
            <div className="card-body p-4">
              <div className="d-flex align-items-center gap-2 mb-3">
                <div style={{ background: '#fef3c7', width: '32px', height: '32px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <User size={18} color="#d97706" />
                </div>
                <h5 className="mb-0 fw-semibold">{t('expenses.sections.approval')}</h5>
              </div>

            <div className="row">
              <div className="col-md-3">
                <div className="info-item">
                  <span className="info-label">{t('expenses.fields.createdBy')}</span>
                  <span className="info-value">{expense.created_by_name}</span>
                </div>
              </div>

              <div className="col-md-3">
                <div className="info-item">
                  <span className="info-label">{t('expenses.fields.createdAt')}</span>
                  <span className="info-value">
                    {new Date(expense.created_at).toLocaleString(isRTL ? 'ar-EG' : 'en-US')}
                  </span>
                </div>
              </div>

              {expense.approved_by_name && (
                <>
                  <div className="col-md-3">
                    <div className="info-item">
                      <span className="info-label">{t('expenses.fields.approvedBy')}</span>
                      <span className="info-value">{expense.approved_by_name}</span>
                    </div>
                  </div>

                  <div className="col-md-3">
                    <div className="info-item">
                      <span className="info-label">{t('expenses.fields.approvedAt')}</span>
                      <span className="info-value">
                        {new Date(expense.approved_at).toLocaleString(isRTL ? 'ar-EG' : 'en-US')}
                      </span>
                    </div>
                  </div>
                </>
              )}

              {expense.approval_notes && (
                <div className="col-12 mt-3">
                  <div className="alert alert-info mb-0">
                    <strong>{t('expenses.fields.approvalNotes')}:</strong> {expense.approval_notes}
                  </div>
                </div>
              )}
            </div>
            </div>
          </div>
        </div>
      </div>

      {/* Approval Modal */}
      <SimpleModal
        isOpen={showApprovalModal}
        onClose={() => setShowApprovalModal(false)}
        title={approvalAction === 'approved' 
          ? t('expenses.modal.approveTitle') 
          : t('expenses.modal.rejectTitle')}
        size="md"
        footer={
          <div className="d-flex gap-2">
            <button
              className="btn btn-secondary"
              onClick={() => setShowApprovalModal(false)}
              disabled={processing}
            >
              {t('common.cancel')}
            </button>
            <button
              className={`btn btn-${approvalAction === 'approved' ? 'success' : 'danger'}`}
              onClick={submitApproval}
              disabled={processing}
            >
              {processing ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" />
                  {t('common.processing')}
                </>
              ) : (
                t('common.confirm')
              )}
            </button>
          </div>
        }
      >
        <div>
          <p>
            {approvalAction === 'approved' 
              ? t('expenses.modal.approveMessage')
              : t('expenses.modal.rejectMessage')}
          </p>
          <div className="mb-3">
            <label className="form-label">{t('expenses.fields.approvalNotes')}</label>
            <textarea
              className="form-input"
              rows="3"
              value={approvalNotes}
              onChange={(e) => setApprovalNotes(e.target.value)}
              placeholder={t('expenses.placeholders.notes')}
            />
          </div>
        </div>
      </SimpleModal>
    </div>
  );
}
