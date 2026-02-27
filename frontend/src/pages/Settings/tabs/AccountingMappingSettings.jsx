import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { GitMerge, Landmark, ShoppingCart, Receipt, Factory, Users, Briefcase, CreditCard, ArrowLeftRight, RefreshCw, AlertTriangle, Calendar } from 'lucide-react';
import api, { accountingAPI } from '../../../utils/api';
import { toastEmitter } from '../../../utils/toastEmitter';

const AccountingMappingSettings = ({ settings, handleSettingChange }) => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const [accounts, setAccounts] = useState([]);
    const [loading, setLoading] = useState(true);

    // Advanced Tools State
    const [fxProcessing, setFxProcessing] = useState(false);
    const [fxDate, setFxDate] = useState(new Date().toISOString().split('T')[0]);
    const [badDebtProcessing, setBadDebtProcessing] = useState(false);
    const [badDebtDays, setBadDebtDays] = useState(90);
    const [leaveProvProcessing, setLeaveProvProcessing] = useState(false);

    useEffect(() => {
        const fetchAccounts = async () => {
            try {
                const response = await api.get('/accounting/accounts');
                setAccounts(response.data || []);
            } catch (err) {
                console.error("Failed to fetch accounts", err);
            } finally {
                setLoading(false);
            }
        };
        fetchAccounts();
    }, []);

    const renderAccountSelect = (label, settingKey, description) => (
        <div className="form-group">
            <label className="form-label text-sm font-medium" htmlFor={settingKey}>{label}</label>
            <select
                id={settingKey}
                className="form-select select select-bordered w-full"
                value={settings[settingKey] || ''}
                onChange={(e) => handleSettingChange(settingKey, e.target.value)}
            >
                <option value="">{t('common.select_account')}</option>
                {accounts.map(acc => (
                    <option key={acc.id} value={acc.id.toString()}>
                        {acc.account_number} - {acc.name}
                    </option>
                ))}
            </select>
            {description && <p className="text-xs text-base-content/40 mt-1">{description}</p>}
        </div>
    );

    // --- Advanced Tools Handlers ---
    const handleFxRevaluation = async () => {
        if (!window.confirm(isRTL ? 'هل تريد تنفيذ إعادة تقييم العملات الأجنبية؟' : 'Run FX revaluation?')) return;
        setFxProcessing(true);
        try {
            await accountingAPI.fxRevaluation({ valuation_date: fxDate });
            toastEmitter.emit(isRTL ? 'تم تنفيذ إعادة تقييم العملات بنجاح' : 'FX Revaluation completed', 'success');
        } catch (err) {
            console.error("FX Revaluation failed", err);
        } finally {
            setFxProcessing(false);
        }
    };

    const handleBadDebtProvision = async () => {
        if (!window.confirm(isRTL ? 'هل تريد إنشاء مخصص ديون مشكوك فيها؟' : 'Create bad debt provision?')) return;
        setBadDebtProcessing(true);
        try {
            await accountingAPI.createBadDebtProvision({ overdue_days: badDebtDays });
            toastEmitter.emit(isRTL ? 'تم إنشاء مخصص الديون المشكوك فيها' : 'Bad debt provision created', 'success');
        } catch (err) {
            console.error("Bad debt provision failed", err);
        } finally {
            setBadDebtProcessing(false);
        }
    };

    const handleLeaveProvision = async () => {
        if (!window.confirm(isRTL ? 'هل تريد إنشاء مخصص إجازات؟' : 'Create leave provision?')) return;
        setLeaveProvProcessing(true);
        try {
            await accountingAPI.createLeaveProvision({});
            toastEmitter.emit(isRTL ? 'تم إنشاء مخصص الإجازات' : 'Leave provision created', 'success');
        } catch (err) {
            console.error("Leave provision failed", err);
        } finally {
            setLeaveProvProcessing(false);
        }
    };

    if (loading) return <div className="p-4 text-center"><span className="loading loading-spinner"></span></div>;

    return (
        <div className="space-y-8">

            {/* ── Sales & Revenue ───────────────────────────── */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <ShoppingCart size={20} className="text-primary" />
                    المبيعات والإيرادات
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {renderAccountSelect('حساب إيرادات المبيعات', 'acc_map_sales_rev', 'يُقيَّد دائناً عند إصدار فواتير البيع')}
                    {renderAccountSelect('تكلفة البضاعة المباعة (COGS)', 'acc_map_cogs', 'يُقيَّد مديناً عند تسليم البضاعة')}
                    {renderAccountSelect('حساب المدينون (AR)', 'acc_map_ar', 'المدينون التجاريون — يُقيَّد مديناً عند البيع')}
                    {renderAccountSelect('حساب الخصم المسموح به', 'acc_map_sales_discount', 'خصومات العملاء من الفواتير')}
                </div>
            </div>

            {/* ── Purchases & AP ────────────────────────────── */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <CreditCard size={20} className="text-primary" />
                    المشتريات والدائنون
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {renderAccountSelect('حساب الدائنون (AP)', 'acc_map_ap', 'الموردون التجاريون — يُقيَّد دائناً عند الشراء')}
                    {renderAccountSelect('حساب مصاريف الشراء', 'acc_map_purchase_exp', 'مصاريف الشحن والجمارك وما شابه')}
                    {renderAccountSelect('حساب خصم المشتريات', 'acc_map_purchase_discount', 'الخصومات الممنوحة من الموردين')}
                </div>
            </div>

            {/* ── Treasury & Cash ───────────────────────────── */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Landmark size={20} className="text-primary" />
                    الخزينة والبنوك
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {renderAccountSelect('الصندوق الرئيسي (نقدي)', 'acc_map_cash_main', 'حسابات النقد الفعلي')}
                    {renderAccountSelect('البنك الرئيسي', 'acc_map_bank', 'الحساب البنكي الافتراضي للتحويلات')}
                    {renderAccountSelect('فروق العملات الأجنبية', 'acc_map_fx_difference', 'أرباح وخسائر تحويل العملات')}
                    {renderAccountSelect('حساب بين الشركات (Intercompany)', 'acc_map_intercompany', 'نقل الأموال بين الشركات التابعة')}
                </div>
            </div>

            {/* ── Inventory ─────────────────────────────────── */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Receipt size={20} className="text-primary" />
                    المخزون والضرائب
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {renderAccountSelect('حساب المخزون', 'acc_map_inventory', 'رصيد المخزون في الميزانية العمومية')}
                    {renderAccountSelect('تسوية المخزون', 'acc_map_inventory_adjustment', 'فروقات الجرد والإتلاف')}
                    {renderAccountSelect('ضريبة القيمة المضافة — مخرجات', 'acc_map_vat_out', 'ضريبة البيع المحصلة')}
                    {renderAccountSelect('ضريبة القيمة المضافة — مدخلات', 'acc_map_vat_in', 'ضريبة الشراء القابلة للاسترداد')}
                    {renderAccountSelect('ضريبة الاستقطاع', 'acc_map_withholding_tax', 'ضريبة الخصم من المصدر')}
                </div>
            </div>

            {/* ── Manufacturing ─────────────────────────────── */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Factory size={20} className="text-primary" />
                    التصنيع
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {renderAccountSelect('المواد الخام', 'acc_map_raw_materials', 'مخزون المواد الأولية قبل الإنتاج')}
                    {renderAccountSelect('إنتاج تحت التشغيل (WIP)', 'acc_map_wip', 'تكاليف الإنتاج غير المكتمل')}
                    {renderAccountSelect('البضاعة تامة الصنع', 'acc_map_finished_goods', 'مخزون المنتجات الجاهزة')}
                    {renderAccountSelect('تكاليف العمالة', 'acc_map_labor_cost', 'أجور العمال المباشرين في الإنتاج')}
                    {renderAccountSelect('التكاليف الصناعية الإضافية (Overhead)', 'acc_map_mfg_overhead', 'تكاليف المصنع الغير مباشرة')}
                </div>
            </div>

            {/* ── HR & Payroll ──────────────────────────────── */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Users size={20} className="text-primary" />
                    الموارد البشرية والرواتب
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {renderAccountSelect('مصاريف الرواتب والأجور', 'acc_map_salaries_exp', 'قيد صرف الرواتب')}
                    {renderAccountSelect('الرواتب المستحقة (Accrued)', 'acc_map_accrued_salaries', 'الرواتب المستحقة غير المدفوعة')}
                    {renderAccountSelect('مكافآت نهاية الخدمة', 'acc_map_eosb', 'مخصص نهاية الخدمة')}
                    {renderAccountSelect('التأمينات الاجتماعية', 'acc_map_social_insurance', 'اشتراكات التأمين الاجتماعي')}
                </div>
            </div>

            {/* ── Projects ──────────────────────────────────── */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Briefcase size={20} className="text-primary" />
                    المشاريع
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {renderAccountSelect('أرباح وخسائر المشاريع عند الإغلاق', 'acc_map_project_pl', 'قيد إقفال المشروع — يُستخدم عند إغلاق المشروع')}
                </div>
            </div>

            {/* ── Fixed Assets ──────────────────────────────── */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <ArrowLeftRight size={20} className="text-primary" />
                    الأصول الثابتة والاستهلاك
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {renderAccountSelect('حساب الأصول الثابتة', 'acc_map_fixed_assets', 'إجمالي الأصول الثابتة')}
                    {renderAccountSelect('مصاريف الاستهلاك', 'acc_map_depreciation_exp', 'قسط الإهلاك الدوري')}
                    {renderAccountSelect('مجمع الاستهلاك', 'acc_map_acc_depreciation', 'الاستهلاك المتجمع — خصم من الأصل')}
                </div>
            </div>

            {/* ── Advanced Accounting Tools ────────────────── */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200" style={{ borderColor: 'var(--warning, #f59e0b)', borderWidth: 2 }}>
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <RefreshCw size={20} style={{ color: 'var(--warning, #f59e0b)' }} />
                    {isRTL ? 'أدوات محاسبية متقدمة' : 'Advanced Accounting Tools'}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* FX Revaluation */}
                    <div style={{ background: 'white', borderRadius: 16, padding: 20, border: '1px solid var(--border-color)' }}>
                        <div style={{ fontWeight: 700, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                            💱 {isRTL ? 'إعادة تقييم العملات' : 'FX Revaluation'}
                        </div>
                        <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 12 }}>
                            {isRTL ? 'تحديث أرصدة العملات الأجنبية بأسعار الصرف الحالية' : 'Update foreign currency balances at current exchange rates'}
                        </p>
                        <input type="date" className="form-input mb-2" value={fxDate} onChange={e => setFxDate(e.target.value)} style={{ fontSize: 13 }} />
                        <button className="btn btn-primary btn-sm btn-block" onClick={handleFxRevaluation} disabled={fxProcessing}>
                            {fxProcessing ? <span className="loading loading-spinner loading-xs"></span> : (isRTL ? 'تنفيذ' : 'Run')}
                        </button>
                    </div>

                    {/* Bad Debt Provision */}
                    <div style={{ background: 'white', borderRadius: 16, padding: 20, border: '1px solid var(--border-color)' }}>
                        <div style={{ fontWeight: 700, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                            ⚠️ {isRTL ? 'مخصص ديون مشكوك فيها' : 'Bad Debt Provision'}
                        </div>
                        <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 12 }}>
                            {isRTL ? 'إنشاء مخصص للفواتير المتأخرة' : 'Create provision for overdue invoices'}
                        </p>
                        <div className="mb-2">
                            <label style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{isRTL ? 'أيام التأخر' : 'Overdue Days'}</label>
                            <input type="number" className="form-input" value={badDebtDays} onChange={e => setBadDebtDays(e.target.value)} style={{ fontSize: 13 }} />
                        </div>
                        <button className="btn btn-warning btn-sm btn-block" onClick={handleBadDebtProvision} disabled={badDebtProcessing}>
                            {badDebtProcessing ? <span className="loading loading-spinner loading-xs"></span> : (isRTL ? 'إنشاء المخصص' : 'Create')}
                        </button>
                    </div>

                    {/* Leave Provision */}
                    <div style={{ background: 'white', borderRadius: 16, padding: 20, border: '1px solid var(--border-color)' }}>
                        <div style={{ fontWeight: 700, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                            🏖️ {isRTL ? 'مخصص إجازات' : 'Leave Provision'}
                        </div>
                        <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 12 }}>
                            {isRTL ? 'حساب وقيد مخصص الإجازات المتراكمة' : 'Calculate and post accrued leave provision'}
                        </p>
                        <button className="btn btn-secondary btn-sm btn-block" onClick={handleLeaveProvision} disabled={leaveProvProcessing} style={{ marginTop: 32 }}>
                            {leaveProvProcessing ? <span className="loading loading-spinner loading-xs"></span> : (isRTL ? 'إنشاء المخصص' : 'Create')}
                        </button>
                    </div>
                </div>
            </div>

            <div className="alert alert-info rounded-xl">
                <GitMerge size={20} />
                <div className="text-sm">
                    تأكد من اختيار الحسابات الصحيحة — هذه الإعدادات تتحكم في القيود المحاسبية التلقائية لجميع العمليات.
                    أي حساب غير محدد سيُوقف إنشاء القيود المرتبطة به.
                </div>
            </div>
        </div>
    );
};

export default AccountingMappingSettings;
