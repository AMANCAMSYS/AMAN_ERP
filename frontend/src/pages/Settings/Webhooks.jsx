import React, { useState, useEffect, useCallback } from 'react';
import { externalAPI } from '../../utils/api';
import '../../components/ModuleStyles.css';

import { formatShortDate, formatDateTime } from '../../utils/dateUtils';

const EMPTY_FORM = {
  name: '',
  url: '',
  events: [],
  retry_count: 3,
  timeout_seconds: 30,
};

export default function Webhooks() {
  const [webhooks, setWebhooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [availableEvents, setAvailableEvents] = useState([]);
  const [showFormModal, setShowFormModal] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [submitting, setSubmitting] = useState(false);
  const [logsWebhook, setLogsWebhook] = useState(null);
  const [logs, setLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(false);

  const fetchWebhooks = useCallback(async () => {
    try {
      setLoading(true);
      const res = await externalAPI.listWebhooks();
      setWebhooks(res.data ?? res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchEvents = useCallback(async () => {
    try {
      const res = await externalAPI.getWebhookEvents();
      setAvailableEvents(res.data ?? res);
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    fetchWebhooks();
    fetchEvents();
  }, [fetchWebhooks, fetchEvents]);

  const openCreate = () => {
    setEditingId(null);
    setForm({ ...EMPTY_FORM });
    setShowFormModal(true);
  };

  const openEdit = (wh) => {
    setEditingId(wh.id);
    setForm({
      name: wh.name || '',
      url: wh.url || '',
      events: wh.events || [],
      retry_count: wh.retry_count ?? 3,
      timeout_seconds: wh.timeout_seconds ?? 30,
    });
    setShowFormModal(true);
  };

  const toggleEvent = (evt) => {
    setForm((prev) => ({
      ...prev,
      events: prev.events.includes(evt)
        ? prev.events.filter((e) => e !== evt)
        : [...prev.events, evt],
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      if (editingId) {
        await externalAPI.updateWebhook(editingId, form);
      } else {
        await externalAPI.createWebhook(form);
      }
      setShowFormModal(false);
      setForm({ ...EMPTY_FORM });
      setEditingId(null);
      fetchWebhooks();
    } catch (err) {
      console.error(err);
      alert('حدث خطأ أثناء الحفظ');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('هل أنت متأكد من حذف هذا الويب هوك؟')) return;
    try {
      await externalAPI.deleteWebhook(id);
      fetchWebhooks();
    } catch (e) {
      console.error(e);
      alert('حدث خطأ أثناء الحذف');
    }
  };

  const handleToggleActive = async (wh) => {
    try {
      await externalAPI.updateWebhook(wh.id, { is_active: !wh.is_active });
      fetchWebhooks();
    } catch (e) {
      console.error(e);
    }
  };

  const openLogs = async (wh) => {
    setLogsWebhook(wh);
    setLogsLoading(true);
    try {
      const res = await externalAPI.getWebhookLogs(wh.id);
      setLogs(res.data ?? res);
    } catch (e) {
      console.error(e);
      setLogs([]);
    } finally {
      setLogsLoading(false);
    }
  };

  const formatDate = (d) => {
    if (!d) return '—';
    return formatShortDate(d);
  };

  return (
    <div className="workspace fade-in">
      <div className="workspace-header">
        <h1 className="workspace-title">الويب هوك</h1>
        <button className="btn btn-primary" onClick={openCreate}>
          + إنشاء ويب هوك جديد
        </button>
      </div>

      {loading ? (
        <p>جاري التحميل...</p>
      ) : webhooks.length === 0 ? (
        <div className="empty-state">لا توجد ويب هوك حالياً</div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>الاسم</th>
              <th>الرابط</th>
              <th>الأحداث</th>
              <th>المحاولات</th>
              <th>المهلة</th>
              <th>الحالة</th>
              <th>إجراءات</th>
            </tr>
          </thead>
          <tbody>
            {webhooks.map((wh) => (
              <tr key={wh.id}>
                <td>{wh.name}</td>
                <td style={{ direction: 'ltr', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {wh.url}
                </td>
                <td>
                  {(wh.events || []).map((ev) => (
                    <span key={ev} className="badge badge-info" style={{ marginInlineEnd: 4, marginBottom: 2, display: 'inline-block' }}>
                      {ev}
                    </span>
                  ))}
                </td>
                <td>{wh.retry_count}</td>
                <td>{wh.timeout_seconds}ث</td>
                <td>
                  {wh.is_active ? (
                    <span className="badge badge-success">مفعّل</span>
                  ) : (
                    <span className="badge badge-danger">معطّل</span>
                  )}
                </td>
                <td style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                  <button className="btn btn-secondary" onClick={() => openEdit(wh)}>
                    تعديل
                  </button>
                  <button className="btn btn-secondary" onClick={() => openLogs(wh)}>
                    السجلات
                  </button>
                  <button
                    className="btn btn-secondary"
                    onClick={() => handleToggleActive(wh)}
                  >
                    {wh.is_active ? 'تعطيل' : 'تفعيل'}
                  </button>
                  <button className="btn btn-danger" onClick={() => handleDelete(wh.id)}>
                    حذف
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Create / Edit Modal */}
      {showFormModal && (
        <div className="modal-overlay" onClick={() => setShowFormModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingId ? 'تعديل الويب هوك' : 'إنشاء ويب هوك جديد'}</h2>
            </div>
            <form onSubmit={handleSubmit}>
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
                      <label>الرابط (URL)</label>
                      <input
                        type="url"
                        value={form.url}
                        onChange={(e) => setForm({ ...form, url: e.target.value })}
                        required
                        style={{ direction: 'ltr' }}
                      />
                    </div>
                    <div className="form-group">
                      <label>عدد المحاولات</label>
                      <input
                        type="number"
                        min={0}
                        value={form.retry_count}
                        onChange={(e) => setForm({ ...form, retry_count: Number(e.target.value) })}
                      />
                    </div>
                    <div className="form-group">
                      <label>المهلة (ثواني)</label>
                      <input
                        type="number"
                        min={1}
                        value={form.timeout_seconds}
                        onChange={(e) => setForm({ ...form, timeout_seconds: Number(e.target.value) })}
                      />
                    </div>
                  </div>
                  <div className="form-group">
                    <label>الأحداث</label>
                    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 4 }}>
                      {availableEvents.length === 0 && <span>لا توجد أحداث متاحة</span>}
                      {availableEvents.map((evt) => {
                        const evtValue = typeof evt === 'string' ? evt : evt.value ?? evt.name ?? evt;
                        return (
                          <label key={evtValue} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                            <input
                              type="checkbox"
                              checked={form.events.includes(evtValue)}
                              onChange={() => toggleEvent(evtValue)}
                            />
                            {evtValue}
                          </label>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <div className="form-actions">
                  <button type="submit" className="btn btn-primary" disabled={submitting}>
                    {submitting ? 'جاري الحفظ...' : editingId ? 'تحديث' : 'إنشاء'}
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => setShowFormModal(false)}
                  >
                    إلغاء
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Logs Modal */}
      {logsWebhook && (
        <div className="modal-overlay" onClick={() => setLogsWebhook(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 800 }}>
            <div className="modal-header">
              <h2>سجلات: {logsWebhook.name}</h2>
            </div>
            <div className="modal-body">
              {logsLoading ? (
                <p>جاري التحميل...</p>
              ) : logs.length === 0 ? (
                <div className="empty-state">لا توجد سجلات</div>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>الحدث</th>
                      <th>رمز الحالة</th>
                      <th>النتيجة</th>
                      <th>المحاولة</th>
                      <th>التاريخ</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((log, idx) => (
                      <tr key={log.id ?? idx}>
                        <td>{log.event}</td>
                        <td style={{ direction: 'ltr' }}>{log.status_code ?? '—'}</td>
                        <td>
                          {log.success ? (
                            <span className="badge badge-success">ناجح</span>
                          ) : (
                            <span className="badge badge-danger">فشل</span>
                          )}
                        </td>
                        <td>{log.attempt ?? '—'}</td>
                        <td>{formatDate(log.created_at ?? log.timestamp)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setLogsWebhook(null)}>
                إغلاق
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
