import { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import DOMPurify from 'dompurify';
import { formatNumber } from '../../utils/format';
import { getCurrency } from '../../utils/auth';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';

// T2.7: HTML-escape user-controlled values before injecting them into the
// print-preview popup. Even though the demo uses a hardcoded sample order,
// printerConfig.companyName / vatNumber and the receipt body originate from
// settings or product names and must not break out of the popup HTML.
function escapeHtml(value) {
    if (value === null || value === undefined) return '';
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

/**
 * POS-002: Thermal Printing Support
 * ESC/POS protocol generator for 80mm and 58mm thermal printers
 * POS-005: Customer Display functionality included
 */

// ESC/POS Command Constants
const ESC = '\x1B';
const GS = '\x1D';
const COMMANDS = {
    INIT: `${ESC}@`,                    // Initialize printer
    CENTER: `${ESC}a\x01`,             // Center alignment
    LEFT: `${ESC}a\x00`,               // Left alignment
    RIGHT: `${ESC}a\x02`,              // Right alignment
    BOLD_ON: `${ESC}E\x01`,            // Bold on
    BOLD_OFF: `${ESC}E\x00`,           // Bold off
    DOUBLE_H: `${GS}!\x10`,            // Double height
    DOUBLE_W: `${GS}!\x20`,            // Double width
    DOUBLE_HW: `${GS}!\x30`,           // Double height + width
    NORMAL: `${GS}!\x00`,              // Normal size
    CUT: `${GS}V\x00`,                 // Full cut
    PARTIAL_CUT: `${GS}V\x01`,         // Partial cut
    FEED_3: '\n\n\n',                    // Feed 3 lines
    OPEN_DRAWER: `${ESC}p\x00\x19\xFA`, // Open cash drawer (pin 2)
    OPEN_DRAWER_2: `${ESC}p\x01\x19\xFA`, // Open cash drawer (pin 5)
    LINE: '━'.repeat(32),
    DASHED_LINE: '-'.repeat(32),
};

function generateReceiptText(order, config = {}) {
    const { companyName = 'AMAN ERP', vatNumber = '', width = 42 } = config;
    const currency = config.currency || 'SAR';
    const lines = order.items || order.lines || [];
    const isSmall = width <= 32;

    const pad = (left, right, w = width) => {
        const space = w - left.length - right.length;
        return left + ' '.repeat(Math.max(1, space)) + right;
    };

    let receipt = '';
    receipt += COMMANDS.INIT;
    receipt += COMMANDS.CENTER;
    receipt += COMMANDS.DOUBLE_HW;
    receipt += companyName + '\n';
    receipt += COMMANDS.NORMAL;
    if (vatNumber) receipt += `الرقم الضريبي: ${vatNumber}\n`;
    receipt += COMMANDS.DASHED_LINE + '\n';

    receipt += COMMANDS.CENTER;
    receipt += COMMANDS.BOLD_ON;
    receipt += `فاتورة ${order.order_number || order.invoice_number || ''}\n`;
    receipt += COMMANDS.BOLD_OFF;
    receipt += `${new Date(order.order_date || order.invoice_date || new Date()).toLocaleString('ar-SA')}\n`;
    if (order.customer_name) receipt += `العميل: ${order.customer_name}\n`;
    receipt += COMMANDS.DASHED_LINE + '\n';

    receipt += COMMANDS.LEFT;
    for (const item of lines) {
        const name = (item.product_name || item.description || '').substring(0, isSmall ? 18 : 26);
        const qty = `${item.quantity}x`;
        const total = formatNumber(item.total || item.quantity * item.unit_price);
        receipt += name + '\n';
        receipt += pad(`  ${qty} @ ${formatNumber(item.unit_price)}`, total) + '\n';
    }

    receipt += COMMANDS.DASHED_LINE + '\n';
    receipt += pad('المجموع الفرعي', formatNumber(order.subtotal || 0)) + '\n';
    if (order.tax_amount > 0) receipt += pad('الضريبة', formatNumber(order.tax_amount)) + '\n';
    if (order.discount > 0) receipt += pad('الخصم', `-${formatNumber(order.discount)}`) + '\n';
    receipt += COMMANDS.LINE + '\n';
    receipt += COMMANDS.BOLD_ON;
    receipt += COMMANDS.DOUBLE_H;
    receipt += pad('الإجمالي', `${formatNumber(order.total || 0)} ${currency}`) + '\n';
    receipt += COMMANDS.NORMAL;
    receipt += COMMANDS.BOLD_OFF;

    if (order.payment_method) {
        receipt += pad('طريقة الدفع', order.payment_method) + '\n';
    }
    if (order.paid_amount > 0) {
        receipt += pad('المدفوع', formatNumber(order.paid_amount)) + '\n';
        const change = order.paid_amount - (order.total || 0);
        if (change > 0) receipt += pad('الباقي', formatNumber(change)) + '\n';
    }

    receipt += COMMANDS.DASHED_LINE + '\n';
    receipt += COMMANDS.CENTER;
    receipt += 'شكراً لتعاملكم معنا\n';
    receipt += 'Thank you for your business\n';
    receipt += COMMANDS.FEED_3;
    receipt += COMMANDS.PARTIAL_CUT;

    return receipt;
}

function ThermalPrintSettings() {
    const { t } = useTranslation();
    const currency = getCurrency();
    const [printerConfig, setPrinterConfig] = useState({
        type: 'browser', // browser, serial, network
        width: '80mm',   // 80mm, 58mm
        ip: '',
        port: 9100,
        companyName: 'AMAN ERP',
        vatNumber: '',
        autoPrint: false,
        openDrawer: true,
    });
    const [testResult, setTestResult] = useState('');
    const previewRef = useRef(null);

    const charWidth = printerConfig.width === '80mm' ? 42 : 32;

    const sampleOrder = {
        order_number: 'POS-2026-001',
        order_date: new Date().toISOString(),
        customer_name: 'عميل عام',
        items: [
            { product_name: 'قهوة عربية', quantity: 2, unit_price: 15, total: 30 },
            { product_name: 'كعكة شوكولاتة', quantity: 1, unit_price: 25, total: 25 },
            { product_name: 'عصير برتقال', quantity: 3, unit_price: 10, total: 30 },
        ],
        subtotal: 85,
        tax_amount: 12.75,
        discount: 0,
        total: 97.75,
        paid_amount: 100,
        payment_method: 'نقدي'
    };

    const handlePrintTest = () => {
        const text = generateReceiptText(sampleOrder, {
            companyName: printerConfig.companyName,
            vatNumber: printerConfig.vatNumber,
            width: charWidth,
            currency
        });

        if (printerConfig.type === 'browser') {
            const cleanText = text.replace(/[\x1B\x1D][\x00-\xFF]/g, '').replace(/[\x00-\x09\x0B\x0C\x0E-\x1F]/g, '');
            const win = window.open('', '_blank', 'width=400,height=600');
            // T2.7: escape the receipt text + width strings before injecting; the
            // body HTML is then sanitized via DOMPurify as defense-in-depth.
            const safeWidth = escapeHtml(printerConfig.width);
            const fontSize = printerConfig.width === '58mm' ? '10px' : '12px';
            const bodyWidth = printerConfig.width === '58mm' ? '220px' : '300px';
            const bodyHtml = escapeHtml(cleanText).replace(/\n/g, '<br>');
            win.document.open();
            win.document.write(
                `<!DOCTYPE html><html dir="rtl"><head><title>Test Receipt</title>` +
                `<style>body { font-family: 'Courier New', monospace; font-size: ${fontSize}; ` +
                `width: ${bodyWidth}; margin: auto; padding: 10px; white-space: pre-wrap; }` +
                `@media print { @page { size: ${safeWidth} auto; margin: 2mm; } }</style>` +
                `</head><body></body></html>`
            );
            win.document.close();
            win.document.body.innerHTML = DOMPurify.sanitize(bodyHtml, { ADD_ATTR: ['style'] });
            setTimeout(() => { win.print(); }, 300);
            setTestResult(t('pos.thermal.test_sent', 'تم إرسال الطباعة التجريبية'));
        } else if (printerConfig.type === 'network') {
            setTestResult(t('pos.thermal.network_info', 'الطباعة عبر الشبكة تتطلب خادم طباعة محلي'));
        }
    };

    const handleOpenDrawer = () => {
        setTestResult(t('pos.thermal.drawer_cmd', 'تم إرسال أمر فتح الدرج'));
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">🖨️ {t('pos.thermal.title', 'إعدادات الطباعة الحرارية')}</h1>
                    <p className="workspace-subtitle">{t('pos.thermal.subtitle', 'تكوين طابعة الإيصالات وشاشة العميل')}</p>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                {/* Settings */}
                <div className="section-card">
                    <h3 className="section-title">{t('pos.thermal.printer_settings', 'إعدادات الطابعة')}</h3>
                    <div className="form-grid">
                        <div className="form-group">
                            <label className="form-label">{t('pos.thermal.connection', 'نوع الاتصال')}</label>
                            <select className="form-input" value={printerConfig.type} onChange={e => setPrinterConfig(p => ({ ...p, type: e.target.value }))}>
                                <option value="browser">{t('pos.thermal.browser', 'طباعة المتصفح')}</option>
                                <option value="network">{t('pos.thermal.network', 'شبكة (TCP/IP)')}</option>
                                <option value="serial">{t('pos.thermal.serial', 'USB/Serial')}</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label className="form-label">{t('pos.thermal.paper_width', 'عرض الورق')}</label>
                            <select className="form-input" value={printerConfig.width} onChange={e => setPrinterConfig(p => ({ ...p, width: e.target.value }))}>
                                <option value="80mm">80mm (42 {t('pos.thermal.chars', 'حرف')})</option>
                                <option value="58mm">58mm (32 {t('pos.thermal.chars', 'حرف')})</option>
                            </select>
                        </div>
                        {printerConfig.type === 'network' && (
                            <>
                                <div className="form-group">
                                    <label className="form-label">{t('pos.thermal.ip', 'عنوان IP')}</label>
                                    <input className="form-input" value={printerConfig.ip} onChange={e => setPrinterConfig(p => ({ ...p, ip: e.target.value }))} placeholder="192.168.1.100" />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">{t('pos.thermal.port', 'المنفذ')}</label>
                                    <input type="number" className="form-input" value={printerConfig.port} onChange={e => setPrinterConfig(p => ({ ...p, port: e.target.value }))} />
                                </div>
                            </>
                        )}
                        <div className="form-group">
                            <label className="form-label">{t('pos.thermal.company_name', 'اسم الشركة')}</label>
                            <input className="form-input" value={printerConfig.companyName} onChange={e => setPrinterConfig(p => ({ ...p, companyName: e.target.value }))} />
                        </div>
                        <div className="form-group">
                            <label className="form-label">{t('pos.thermal.vat', 'الرقم الضريبي')}</label>
                            <input className="form-input" value={printerConfig.vatNumber} onChange={e => setPrinterConfig(p => ({ ...p, vatNumber: e.target.value }))} />
                        </div>
                        <div className="form-group">
                            <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <input type="checkbox" checked={printerConfig.autoPrint} onChange={e => setPrinterConfig(p => ({ ...p, autoPrint: e.target.checked }))} />
                                {t('pos.thermal.auto_print', 'طباعة تلقائية بعد كل طلب')}
                            </label>
                        </div>
                        <div className="form-group">
                            <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <input type="checkbox" checked={printerConfig.openDrawer} onChange={e => setPrinterConfig(p => ({ ...p, openDrawer: e.target.checked }))} />
                                {t('pos.thermal.open_drawer', 'فتح درج النقود تلقائياً')}
                            </label>
                        </div>
                    </div>
                    <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
                        <button className="btn btn-primary" onClick={handlePrintTest}>🖨️ {t('pos.thermal.test_print', 'طباعة تجريبية')}</button>
                        <button className="btn btn-secondary" onClick={handleOpenDrawer}>💰 {t('pos.thermal.open_drawer_btn', 'فتح الدرج')}</button>
                    </div>
                    {testResult && <div className="alert alert-info" style={{ marginTop: 8 }}>{testResult}</div>}
                </div>

                {/* Preview */}
                <div className="section-card">
                    <h3 className="section-title">{t('pos.thermal.preview', 'معاينة الإيصال')}</h3>
                    <div ref={previewRef} style={{
                        background: '#fff', border: '1px solid #ddd', borderRadius: 8,
                        padding: 16, fontFamily: "'Courier New', monospace",
                        fontSize: printerConfig.width === '58mm' ? 10 : 12,
                        width: printerConfig.width === '58mm' ? 220 : 300,
                        margin: 'auto', direction: 'rtl', whiteSpace: 'pre-wrap', lineHeight: 1.6
                    }}>
                        <div style={{ textAlign: 'center', fontWeight: 700, fontSize: '1.3em' }}>{printerConfig.companyName}</div>
                        {printerConfig.vatNumber && <div style={{ textAlign: 'center', fontSize: '0.85em' }}>الرقم الضريبي: {printerConfig.vatNumber}</div>}
                        <div style={{ borderTop: '1px dashed #000', margin: '6px 0' }} />
                        <div style={{ textAlign: 'center', fontWeight: 600 }}>فاتورة POS-2026-001</div>
                        <div style={{ textAlign: 'center', fontSize: '0.85em' }}>{new Date().toLocaleString('ar-SA')}</div>
                        <div style={{ borderTop: '1px dashed #000', margin: '6px 0' }} />
                        {sampleOrder.items.map((item, i) => (
                            <div key={i}>
                                <div>{item.product_name}</div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span>  {item.quantity}x @ {formatNumber(item.unit_price)}</span>
                                    <span>{formatNumber(item.total)}</span>
                                </div>
                            </div>
                        ))}
                        <div style={{ borderTop: '1px dashed #000', margin: '6px 0' }} />
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>{t('pos.receipt.subtotal')}</span><span>{formatNumber(sampleOrder.subtotal)}</span></div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>{t('pos.receipt.tax')}</span><span>{formatNumber(sampleOrder.tax_amount)}</span></div>
                        <div style={{ borderTop: '2px solid #000', margin: '4px 0' }} />
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, fontSize: '1.2em' }}><span>{t('pos.receipt.total')}</span><span>{formatNumber(sampleOrder.total)} {currency}</span></div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>{t('pos.receipt.paid')}</span><span>{formatNumber(100)}</span></div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>{t('pos.receipt.balance_due')}</span><span>{formatNumber(2.25)}</span></div>
                        <div style={{ borderTop: '1px dashed #000', margin: '6px 0' }} />
                        <div style={{ textAlign: 'center', fontSize: '0.85em' }}>شكراً لتعاملكم معنا</div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export { generateReceiptText, COMMANDS };
export default ThermalPrintSettings;
