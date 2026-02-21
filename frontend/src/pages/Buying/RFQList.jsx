import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { purchasesAPI, inventoryAPI } from '../../utils/api';
import { useToast } from '../../context/ToastContext';
import { getCurrency } from '../../utils/auth';
import { Plus, Send, GitCompare, ArrowRightCircle, FileText, ChevronDown, X } from 'lucide-react';
import '../../components/ModuleStyles.css';

import DateInput from '../../components/common/DateInput';
const RFQList = () => {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    const { showToast } = useToast();
    const currency = getCurrency();
    const isRTL = i18n.language === 'ar';
    const [rfqs, setRfqs] = useState([]);
    const [suppliers, setSuppliers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [form, setForm] = useState({ title: '', supplier_ids: [], deadline: '', notes: '' });
    const [supplierDropOpen, setSupplierDropOpen] = useState(false);
    const [supplierSearch, setSupplierSearch] = useState('');
    const supplierDropRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (e) => {
            if (supplierDropRef.current && !supplierDropRef.current.contains(e.target)) {
                setSupplierDropOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    useEffect(() => { fetchRFQs(); fetchSuppliers(); }, []);

    const fetchSuppliers = async () => {
        try { const res = await inventoryAPI.listSuppliers({ limit: 1000 }); setSuppliers(res.data || []); }
        catch (err) { console.error(err); }
    };

    const fetchRFQs = async () => {
        try { setLoading(true); const res = await purchasesAPI.listRFQs(); setRfqs(res.data || []); }
        catch (err) { console.error(err); } finally { setLoading(false); }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        if (form.supplier_ids.length === 0) { showToast(t('buying.rfq.select_supplier_required'), 'error'); return; }
        try {
            await purchasesAPI.createRFQ({ title: form.title, supplier_ids: form.supplier_ids, deadline: form.deadline || null, notes: form.notes || null });
            showToast(t('buying.rfq_created'), 'success');
            setShowModal(false); setForm({ title: '', supplier_ids: [], deadline: '', notes: '' }); fetchRFQs();
        } catch (err) { showToast(err.response?.data?.detail || t('common.error'), 'error'); }
    };

    const handleSend = async (id) => {
        try { await purchasesAPI.sendRFQ(id); showToast(t('buying.rfq_sent'), 'success'); fetchRFQs(); }
        catch (err) { showToast(t('common.error'), 'error'); }
    };

    const handleCompare = async (id) => {
        try {
            const res = await purchasesAPI.compareRFQ(id);
            showToast(t('buying.rfq_compared_best') + (res.data?.best_supplier || '—'), 'success');
        } catch (err) { showToast(t('common.error'), 'error'); }
    };

    const handleConvert = async (id) => {
        try {
            await purchasesAPI.convertRFQtoPO(id, {});
            showToast(t('buying.rfq_converted_to_po'), 'success'); fetchRFQs();
        } catch (err) { showToast(err.response?.data?.detail || t('common.error'), 'error'); }
    };

    const statusBadge = (s) => {
        const map = { draft: 'bg-gray-100 text-gray-600', sent: 'bg-blue-100 text-blue-700', received: 'bg-purple-100 text-purple-700', compared: 'bg-yellow-100 text-yellow-700', converted: 'bg-green-100 text-green-700' };
        const labels = { draft: t('buying.rfq_status_draft'), sent: t('buying.rfq_status_sent'), received: t('buying.rfq_status_received'), compared: t('buying.rfq_status_compared'), converted: t('buying.rfq_status_converted') };
        return <span className={`badge ${map[s] || 'bg-gray-100'}`}>{labels[s] || s}</span>;
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className="workspace-title"><span className="p-2 rounded-lg bg-indigo-50 text-indigo-600"><FileText size={24} /></span> {t('buying.rfq_title')}</h1>
                        <p className="workspace-subtitle">{t('buying.rfq_subtitle')}</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => setShowModal(true)}><Plus size={18} /> {t('buying.new_rfq')}</button>
                </div>
            </div>

            <div className="card section-card">
                {loading ? <div className="text-center p-4">...</div> : (
                    <div className="data-table-container">
                        <table className="data-table">
                            <thead><tr>
                                <th>#</th>
                                <th>{t('buying.rfq_col_title')}</th>
                                <th>{t('buying.rfq_col_status')}</th>
                                <th>{t('buying.rfq_col_deadline')}</th>
                                <th>{t('buying.rfq_col_responses')}</th>
                                <th>{t('buying.rfq_col_actions')}</th>
                            </tr></thead>
                            <tbody>
                                {rfqs.map(rfq => (
                                    <tr key={rfq.id}>
                                        <td>{rfq.id}</td>
                                        <td className="font-semibold">{rfq.title}</td>
                                        <td>{statusBadge(rfq.status)}</td>
                                        <td>{rfq.deadline || '—'}</td>
                                        <td>{rfq.response_count || 0}</td>
                                        <td>
                                            <div className="d-flex gap-2">
                                                {rfq.status === 'draft' && <button className="btn btn-sm btn-primary" onClick={() => handleSend(rfq.id)} title={t('buying.send')}><Send size={14} /></button>}
                                                {(rfq.status === 'received' || rfq.status === 'sent') && <button className="btn btn-sm btn-warning" onClick={() => handleCompare(rfq.id)} title={t('buying.compare')}><GitCompare size={14} /></button>}
                                                {rfq.status === 'compared' && <button className="btn btn-sm btn-success" onClick={() => handleConvert(rfq.id)} title={t('buying.convert_to_po')}><ArrowRightCircle size={14} /></button>}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                                {rfqs.length === 0 && <tr><td colSpan="6" className="text-center text-muted p-4">{t('buying.no_rfqs')}</td></tr>}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
                        <h3 className="modal-title">{t('buying.new_rfq_modal')}</h3>
                        <form onSubmit={handleCreate} className="space-y-4">
                            <div className="form-group"><label className="form-label">{t('buying.rfq_col_title')}</label>
                                <input className="form-input" required value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} /></div>
                            <div className="form-group" style={{ position: 'relative' }} ref={supplierDropRef}>
                                <label className="form-label">{t('buying.rfq.suppliers')}</label>
                                {/* chips */}
                                {form.supplier_ids.length > 0 && (
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 6 }}>
                                        {form.supplier_ids.map(id => {
                                            const s = suppliers.find(x => x.id === id);
                                            if (!s) return null;
                                            return (
                                                <span key={id} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, background: 'var(--primary)', color: '#fff', borderRadius: 20, padding: '3px 10px', fontSize: 13 }}>
                                                    {s.name || s.supplier_name}
                                                    <button type="button" onClick={() => setForm(prev => ({ ...prev, supplier_ids: prev.supplier_ids.filter(x => x !== id) }))} style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer', padding: 0, display: 'flex', alignItems: 'center' }}><X size={13} /></button>
                                                </span>
                                            );
                                        })}
                                    </div>
                                )}
                                {/* trigger */}
                                <div
                                    className="form-input"
                                    style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer', userSelect: 'none' }}
                                    onClick={() => { setSupplierDropOpen(o => !o); setSupplierSearch(''); }}
                                >
                                    <span style={{ color: form.supplier_ids.length ? 'var(--text-main)' : 'var(--text-muted)' }}>
                                        {form.supplier_ids.length ? `${form.supplier_ids.length} ${t('buying.rfq.supplier_selected')}` : t('buying.rfq.choose_suppliers')}
                                    </span>
                                    <ChevronDown size={16} style={{ color: 'var(--text-muted)', transition: 'transform .2s', transform: supplierDropOpen ? 'rotate(180deg)' : 'rotate(0deg)' }} />
                                </div>
                                {/* dropdown */}
                                {supplierDropOpen && (
                                    <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 999, background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 8, boxShadow: '0 8px 24px rgba(0,0,0,.12)', marginTop: 4 }}>
                                        <div style={{ padding: '8px 10px', borderBottom: '1px solid var(--border-color)' }}>
                                            <input
                                                autoFocus
                                                className="form-input"
                                                style={{ padding: '6px 10px', fontSize: 13 }}
                                                placeholder={t('buying.rfq.search_supplier')}
                                                value={supplierSearch}
                                                onChange={e => setSupplierSearch(e.target.value)}
                                                onClick={e => e.stopPropagation()}
                                            />
                                        </div>
                                        <div style={{ maxHeight: 220, overflowY: 'auto' }}>
                                            {suppliers
                                                .filter(s => (s.name || s.supplier_name || '').toLowerCase().includes(supplierSearch.toLowerCase()) || (s.party_code || '').toLowerCase().includes(supplierSearch.toLowerCase()))
                                                .map(s => {
                                                    const selected = form.supplier_ids.includes(s.id);
                                                    return (
                                                        <div
                                                            key={s.id}
                                                            onClick={() => {
                                                                setForm(prev => ({
                                                                    ...prev,
                                                                    supplier_ids: selected
                                                                        ? prev.supplier_ids.filter(x => x !== s.id)
                                                                        : [...prev.supplier_ids, s.id]
                                                                }));
                                                            }}
                                                            style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '9px 14px', cursor: 'pointer', background: selected ? 'rgba(37,99,235,.07)' : 'transparent', borderBottom: '1px solid var(--border-color)' }}
                                                            onMouseEnter={e => { if (!selected) e.currentTarget.style.background = 'var(--bg-hover)'; }}
                                                            onMouseLeave={e => { e.currentTarget.style.background = selected ? 'rgba(37,99,235,.07)' : 'transparent'; }}
                                                        >
                                                            <div style={{ width: 18, height: 18, borderRadius: 4, border: `2px solid ${selected ? 'var(--primary)' : 'var(--border-color)'}`, background: selected ? 'var(--primary)' : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                                                                {selected && <svg width="11" height="9" viewBox="0 0 11 9" fill="none"><path d="M1 4l3 3 6-6" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>}
                                                            </div>
                                                            <span style={{ fontSize: 14 }}>{s.name || s.supplier_name}</span>
                                                            {s.party_code && <span style={{ marginInlineStart: 'auto', color: 'var(--primary)', fontFamily: 'monospace', fontSize: 12 }}>{s.party_code}</span>}
                                                        </div>
                                                    );
                                                })
                                            }
                                            {suppliers.filter(s => (s.name || s.supplier_name || '').toLowerCase().includes(supplierSearch.toLowerCase())).length === 0 &&
                                                <div style={{ padding: '12px 14px', color: 'var(--text-muted)', fontSize: 13, textAlign: 'center' }}>{t('buying.rfq.no_results')}</div>}
                                        </div>
                                        <div style={{ padding: '8px 12px', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'flex-end' }}>
                                            <button type="button" className="btn btn-sm btn-primary" onClick={() => setSupplierDropOpen(false)}>{t('common.confirm')}</button>
                                        </div>
                                    </div>
                                )}
                                {form.supplier_ids.length === 0 && <small style={{ color: 'var(--danger)' }}>{t('buying.rfq.select_supplier_required')}</small>}
                            </div>
                            <div className="form-group"><label className="form-label">{t('buying.rfq_col_deadline')}</label>
                                <DateInput className="form-input" value={form.deadline} onChange={e => setForm({ ...form, deadline: e.target.value })} /></div>
                            <div className="form-group"><label className="form-label">{t('buying.rfq_notes')}</label>
                                <textarea className="form-input" rows="2" value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} /></div>
                            <div className="d-flex gap-3 pt-3">
                                <button type="submit" className="btn btn-primary flex-1">{t('buying.create')}</button>
                                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>{t('buying.cancel')}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default RFQList;
