import { useState, useEffect } from 'react';
import { expensesAPI } from '../../utils/api';
import { useToast } from '../../context/ToastContext';
import { useBranch } from '../../context/BranchContext';
import { Search, Plus, Filter, Clock, CheckCircle, XCircle, Receipt } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import BackButton from '../../components/common/BackButton';
import { useTranslation } from 'react-i18next';
import { formatNumber } from '../../utils/format';
import { getCurrency } from '../../utils/auth';
import CustomDatePicker from '../../components/common/CustomDatePicker';
import Pagination, { usePagination } from '../../components/common/Pagination';
import { formatShortDate } from '../../utils/dateUtils';


export default function ExpenseList() {
  const { t, i18n } = useTranslation();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const { currentBranch, loading: branchLoading } = useBranch();
  const isRTL = i18n.language === 'ar';
  const currency = getCurrency() || '';

  const [expenses, setExpenses] = useState([]);
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState({
    expense_type: '',
    approval_status: '',
    start_date: '',
    end_date: ''
  });

  useEffect(() => {
    if (!branchLoading) {
      loadData();
    }
  }, [currentBranch, branchLoading, filters]);

  const loadData = async () => {
    try {
      setLoading(true);
      const params = { ...filters };
      if (currentBranch) params.branch_id = currentBranch.id;
      
      const [expensesRes, summaryRes] = await Promise.all([
        expensesAPI.list(params),
        expensesAPI.summary(params)
      ]);
      setExpenses(expensesRes.data || []);
      setSummary(summaryRes.data || []);
    } catch (error) {
      showToast(t('expenses.errors.loadFailed'), 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    try {
      const res = await expensesAPI.list({ ...filters, search });
      setExpenses(res.data || []);
    } catch (error) {
      showToast(t('expenses.errors.searchFailed'), 'error');
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
      <span style={{ background: s.bg, color: s.color, padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '600', whiteSpace: 'nowrap' }}>
        {s.icon} {t(`expenses.status.${status}`)}
      </span>
    );
  };

  const getTypeBadge = (type) => {
    const colors = {
      materials: '#3b82f6', labor: '#8b5cf6', services: '#06b6d4',
      travel: '#f59e0b', rent: '#ec4899', utilities: '#10b981',
      salaries: '#6366f1', other: '#6b7280'
    };
    const color = colors[type] || '#6b7280';
    return (
      <span style={{ background: `${color}15`, color, padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: '600' }}>
        {t(`expenses.types.${type}`, type)}
      </span>
    );
  };

  const filteredExpenses = expenses.filter(exp =>
    !search ||
    exp.expense_number?.toLowerCase().includes(search.toLowerCase()) ||
    exp.description?.toLowerCase().includes(search.toLowerCase()) ||
    exp.vendor_name?.toLowerCase().includes(search.toLowerCase())
  );

  const { currentPage, pageSize, totalItems, paginatedItems, onPageChange, onPageSizeChange } = usePagination(filteredExpenses);

  return (
    <div className="workspace fade-in">
      {/* Header */}
      <div className="workspace-header">
        <BackButton />
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ background: 'linear-gradient(135deg, #f43f5e 0%, #e11d48 100%)', width: '42px', height: '42px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Receipt size={22} color="#fff" />
            </div>
            <div>
              <h1 className="workspace-title">{t('expenses.title')}</h1>
              <p className="text-muted small mb-0">{t('expenses.subtitle')}</p>
            </div>
          </div>
          <button className="btn btn-primary d-flex align-items-center gap-2" onClick={() => navigate('/expenses/new')}>
            <Plus size={18} />
            {t('expenses.addNew')}
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="metrics-grid mb-4">
        <div className="metric-card">
          <div className="metric-label">{t('expenses.metrics.total')}</div>
          <div className="metric-value text-primary">
            {formatNumber(summary.total_amount || 0)} <small>{currency}</small>
          </div>
          <div className="metric-change text-muted">{summary.total_expenses || 0} {t('expenses.metrics.totalLabel')}</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">{t('expenses.metrics.pending')}</div>
          <div className="metric-value text-warning">
            {formatNumber(summary.pending_amount || 0)} <small>{currency}</small>
          </div>
          <div className="metric-change text-muted">{summary.pending_approval || 0} {t('expenses.metrics.pendingCount')}</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">{t('expenses.metrics.approved')}</div>
          <div className="metric-value text-success">
            {formatNumber(summary.approved_amount || 0)} <small>{currency}</small>
          </div>
          <div className="metric-change text-muted">{summary.approved || 0} {t('expenses.metrics.approvedCount')}</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">{t('expenses.metrics.rejected')}</div>
          <div className="metric-value text-danger">
            {summary.rejected || 0}
          </div>
        </div>
      </div>

      {/* Quick Navigation Cards */}
      <div className="modules-grid" style={{ gap: '16px', marginBottom: '16px' }}>

        {/* Quick Actions */}
        <div className="card">
          <h3 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
            ⚡ {t('expenses.quick_actions', 'الإجراءات السريعة')}
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '12px' }}>
            <button className="btn btn-primary btn-sm" onClick={() => navigate('/expenses/new')} style={{ textAlign: 'center', fontSize: '13px', padding: '10px 8px' }}>
              <Plus size={14} /> {t('expenses.addNew')}
            </button>
            <button className="btn btn-outline" onClick={() => setFilters({ ...filters, approval_status: 'pending' })} style={{ textAlign: 'center', fontSize: '13px', padding: '10px 8px' }}>
              <Clock size={14} /> {t('expenses.status.pending')}
            </button>
          </div>
        </div>

        {/* Status Summary */}
        <div className="card">
          <h3 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
            📊 {t('expenses.status_summary', 'ملخص الحالة')}
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', marginTop: '12px' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '2px' }}>{t('expenses.status.pending')}</div>
              <div style={{ fontSize: '20px', fontWeight: '700', color: '#d97706' }}>{summary.pending_approval || 0}</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '2px' }}>{t('expenses.status.approved')}</div>
              <div style={{ fontSize: '20px', fontWeight: '700', color: '#16a34a' }}>{summary.approved || 0}</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '2px' }}>{t('expenses.status.rejected')}</div>
              <div style={{ fontSize: '20px', fontWeight: '700', color: '#dc2626' }}>{summary.rejected || 0}</div>
            </div>
          </div>
        </div>

        {/* Filters Shortcut */}
        <div className="card">
          <h3 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
            🔍 {t('common.filter', 'تصفية')}
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '8px', marginTop: '12px' }}>
            <button className="btn btn-outline" onClick={() => { setFilters({ expense_type: '', approval_status: '', start_date: '', end_date: '' }); setSearch(''); }} style={{ textAlign: 'center', fontSize: '13px', padding: '9px 8px' }}>
              ✕ {t('common.clear_filters', 'مسح الفلاتر')}
            </button>
            <button className="btn btn-outline" onClick={() => setFilters({ ...filters, approval_status: 'approved' })} style={{ textAlign: 'center', fontSize: '13px', padding: '9px 8px' }}>
              ✅ {t('expenses.status.approved')}
            </button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card mb-4">
        <div >
          <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
            <div style={{ minWidth: '140px', flex: 1 }}>
              <label className="form-label small fw-semibold mb-1">{t('expenses.fields.type')}</label>
              <select className="form-input" value={filters.expense_type}
                onChange={(e) => setFilters({ ...filters, expense_type: e.target.value })}>
                <option value="">{t('common.all')}</option>
                <option value="materials">{t('expenses.types.materials')}</option>
                <option value="labor">{t('expenses.types.labor')}</option>
                <option value="services">{t('expenses.types.services')}</option>
                <option value="travel">{t('expenses.types.travel')}</option>
                <option value="rent">{t('expenses.types.rent')}</option>
                <option value="utilities">{t('expenses.types.utilities')}</option>
                <option value="salaries">{t('expenses.types.salaries')}</option>
                <option value="other">{t('expenses.types.other')}</option>
              </select>
            </div>

            <div style={{ minWidth: '120px', flex: 1 }}>
              <label className="form-label small fw-semibold mb-1">{t('expenses.fields.status')}</label>
              <select className="form-input" value={filters.approval_status}
                onChange={(e) => setFilters({ ...filters, approval_status: e.target.value })}>
                <option value="">{t('common.all')}</option>
                <option value="pending">{t('expenses.status.pending')}</option>
                <option value="approved">{t('expenses.status.approved')}</option>
                <option value="rejected">{t('expenses.status.rejected')}</option>
              </select>
            </div>

            <div style={{ width: '180px' }}>
              <CustomDatePicker
                label={t('common.start_date')}
                selected={filters.start_date}
                onChange={(val) => setFilters({ ...filters, start_date: val })}
                placeholder="YYYY/MM/DD"
                isClearable
              />
            </div>

            <div style={{ width: '180px' }}>
              <CustomDatePicker
                label={t('common.end_date')}
                selected={filters.end_date}
                onChange={(val) => setFilters({ ...filters, end_date: val })}
                placeholder="YYYY/MM/DD"
                isClearable
              />
            </div>

            <button className="btn btn-primary btn-sm d-flex align-items-center gap-1" style={{ height: '38px', whiteSpace: 'nowrap' }} onClick={loadData}>
              <Filter size={14} />
              {t('common.filter')}
            </button>

            <div style={{ width: '260px' }}>
              <div style={{ position: 'relative' }}>
                <Search size={16} style={{ position: 'absolute', top: '50%', transform: 'translateY(-50%)', color: '#9ca3af', ...(isRTL ? { left: '12px' } : { right: '12px' }) }} />
                <input type="text" className="form-input" style={{ ...(isRTL ? { paddingLeft: '36px' } : { paddingRight: '36px' }) }}
                  placeholder={t('expenses.searchPlaceholder')}
                  value={search} onChange={(e) => setSearch(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card">
        {loading ? (
          <div className="card-body text-center py-5">
            <div className="spinner-border text-primary" role="status" />
            <p className="text-muted mt-2 mb-0">{t('common.loading')}</p>
          </div>
        ) : filteredExpenses.length === 0 ? (
          <div className="card-body text-center py-5">
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>📋</div>
            <h5 className="text-muted">{t('expenses.noExpenses')}</h5>
            <button className="btn btn-primary btn-sm mt-3" onClick={() => navigate('/expenses/new')}>
              <Plus size={16} className="me-1" />
              {t('expenses.addNew')}
            </button>
          </div>
        ) : (
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('expenses.fields.number')}</th>
                  <th>{t('expenses.fields.date')}</th>
                  <th>{t('expenses.fields.type')}</th>
                  <th>{t('expenses.fields.vendor')}</th>
                  <th>{t('expenses.fields.description')}</th>
                  <th style={{ textAlign: isRTL ? 'left' : 'right' }}>{t('expenses.fields.amount')}</th>
                  <th>{t('expenses.fields.status')}</th>
                  <th>{t('common.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {paginatedItems.map((expense) => (
                  <tr key={expense.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/expenses/${expense.id}`)}>
                    <td>
                      <span className="fw-bold" style={{ color: 'var(--primary)' }}>{expense.expense_number}</span>
                    </td>
                    <td style={{ whiteSpace: 'nowrap' }}>
                      {formatShortDate(expense.expense_date)}
                    </td>
                    <td>{getTypeBadge(expense.expense_type)}</td>
                    <td>{expense.vendor_name || <span className="text-muted">—</span>}</td>
                    <td>
                      <div className="text-truncate" style={{ maxWidth: '180px' }}>
                        {expense.description || <span className="text-muted">—</span>}
                      </div>
                    </td>
                    <td style={{ textAlign: isRTL ? 'left' : 'right', fontWeight: '700', whiteSpace: 'nowrap' }}>
                      {formatNumber(expense.amount)} <span className="text-muted fw-normal small">{currency}</span>
                    </td>
                    <td>{getStatusBadge(expense.approval_status)}</td>
                    <td>
                      <button
                        className="btn btn-sm btn-outline-primary"
                        onClick={(e) => { e.stopPropagation(); navigate(`/expenses/${expense.id}`); }}
                        style={{ borderRadius: '8px', fontSize: '12px' }}
                      >
                        {t('common.view')}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <Pagination currentPage={currentPage} totalItems={totalItems} pageSize={pageSize} onPageChange={onPageChange} onPageSizeChange={onPageSizeChange} />
          </div>
        )}
      </div>
    </div>
  );
}
