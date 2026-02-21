import React, { useState, useEffect, useCallback } from 'react';
import { externalAPI } from '../../utils/api';
import '../../components/ModuleStyles.css';

import { formatShortDate, formatDateTime } from '../../utils/dateUtils';

const PERMISSION_OPTIONS = ['read', 'write', 'invoices', 'reports', 'inventory'];

export default function ApiKeys() {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKeyResult, setNewKeyResult] = useState(null);
  const [form, setForm] = useState({
    name: '',
    permissions: [],
    rate_limit_per_minute: 60,
    expires_at: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchKeys = useCallback(async () => {
    try {
      setLoading(true);
      const res = await externalAPI.listApiKeys();
      setKeys(res.data ?? res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchKeys();
  }, [fetchKeys]);

  const togglePermission = (perm) => {
    setForm((prev) => ({
      ...prev,
      permissions: prev.permissions.includes(perm)
        ? prev.permissions.filter((p) => p !== perm)
        : [...prev.permissions, perm],
    }));
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      const payload = {
        ...form,
        expires_at: form.expires_at || null,
      };
      const res = await externalAPI.createApiKey(payload);
      const result = res.data ?? res;
      setNewKeyResult(result);
      setShowCreateModal(false);
      setForm({ name: '', permissions: [], rate_limit_per_minute: 60, expires_at: '' });
      fetchKeys();
    } catch (e) {
      console.error(e);
      alert('حدث خطأ أثناء إنشاء المفتاح');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('هل أنت متأكد من حذف هذا المفتاح؟')) return;
    try {
      await externalAPI.deleteApiKey(id);
      fetchKeys();
    } catch (e) {
      console.error(e);
      alert('حدث خطأ أثناء الحذف');
    }
  };

  const formatDate = (d) => {
    if (!d) return '—';
    return formatShortDate(d);
  };

  return (
    <div className="workspace fade-in">
      <div className="workspace-header">
        <h1 className="workspace-title">مفاتيح API</h1>
        <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
          + إنشاء مفتاح جديد
        </button>
      </div>

      {newKeyResult?.key && (
        <div
          style={{
            background: '#d4edda',
            border: '2px solid #28a745',
            borderRadius: 8,
            padding: 16,
            marginBottom: 16,
          }}
        >
          <strong>⚠️ تم إنشاء المفتاح بنجاح — انسخه الآن، لن يظهر مرة أخرى:</strong>
          <pre
            style={{
              background: '#fff',
              padding: 12,
              borderRadius: 4,
              marginTop: 8,
              wordBreak: 'break-all',
              whiteSpace: 'pre-wrap',
              direction: 'ltr',
              textAlign: 'left',
            }}
          >
            {newKeyResult.key}
          </pre>
          <button className="btn btn-secondary" onClick={() => setNewKeyResult(null)}>
            إغلاق
          </button>
        </div>
      )}

      {loading ? (
        <p>جاري التحميل...</p>
      ) : keys.length === 0 ? (
        <div className="empty-state">لا توجد مفاتيح API حالياً</div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>الاسم</th>
              <th>البادئة</th>
              <th>الصلاحيات</th>
              <th>الحد</th>
              <th>تاريخ الانتهاء</th>
              <th>آخر استخدام</th>
              <th>عدد الاستخدام</th>
              <th>الحالة</th>
              <th>إجراءات</th>
            </tr>
          </thead>
          <tbody>
            {keys.map((k) => (
              <tr key={k.id}>
                <td>{k.name}</td>
                <td style={{ direction: 'ltr', fontFamily: 'monospace' }}>{k.key_prefix}</td>
                <td>
                  {(k.permissions || []).map((p) => (
                    <span key={p} className="badge badge-info" style={{ marginInlineEnd: 4 }}>
                      {p}
                    </span>
                  ))}
                </td>
                <td>{k.rate_limit_per_minute}</td>
                <td>{formatDate(k.expires_at)}</td>
                <td>{formatDate(k.last_used_at)}</td>
                <td>{k.usage_count ?? 0}</td>
                <td>
                  {k.is_active ? (
                    <span className="badge badge-success">مفعّل</span>
                  ) : (
                    <span className="badge badge-danger">معطّل</span>
                  )}
                </td>
                <td>
                  <button className="btn btn-danger" onClick={() => handleDelete(k.id)}>
                    حذف
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>إنشاء مفتاح API جديد</h2>
            </div>
            <form onSubmit={handleCreate}>
              <div className="modal-body">
                <div className="form-section">
                  <div className="form-grid">
                    <div className="form-group">
                      <label>الاسم</label>
                      <input
                        type="text"
                        value={form.name}
                        onChange={(e) => setForm({ ...form, name: e.target.value })}
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label>الحد لكل دقيقة</label>
                      <input
                        type="number"
                        min={1}
                        value={form.rate_limit_per_minute}
                        onChange={(e) =>
                          setForm({ ...form, rate_limit_per_minute: Number(e.target.value) })
                        }
                      />
                    </div>
                    <div className="form-group">
                      <label>تاريخ الانتهاء (اختياري)</label>
                      <input
                        type="date"
                        value={form.expires_at}
                        onChange={(e) => setForm({ ...form, expires_at: e.target.value })}
                      />
                    </div>
                  </div>
                  <div className="form-group">
                    <label>الصلاحيات</label>
                    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 4 }}>
                      {PERMISSION_OPTIONS.map((perm) => (
                        <label key={perm} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                          <input
                            type="checkbox"
                            checked={form.permissions.includes(perm)}
                            onChange={() => togglePermission(perm)}
                          />
                          {perm}
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <div className="form-actions">
                  <button type="submit" className="btn btn-primary" disabled={submitting}>
                    {submitting ? 'جاري الإنشاء...' : 'إنشاء'}
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => setShowCreateModal(false)}
                  >
                    إلغاء
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
