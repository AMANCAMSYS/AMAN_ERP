import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import { selfServiceAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import { formatNumber } from '../../utils/format';
import { getCurrency } from '../../utils/auth';
import BackButton from '../../components/common/BackButton';
import '../../components/ModuleStyles.css';

const PayslipDetail = () => {
    const { t } = useTranslation();
    const { id } = useParams();
    const currency = getCurrency();
    const [payslip, setPayslip] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchPayslip();
    }, [id]);

    const fetchPayslip = async () => {
        setLoading(true);
        try {
            const res = await selfServiceAPI.getPayslip(id);
            setPayslip(res.data?.data || res.data);
        } catch (err) {
            toastEmitter.emit(t('common.error'), 'error');
        } finally {
            setLoading(false);
        }
    };

    const fmt = (v) => formatNumber(v || 0);

    if (loading) return <div className="module-loading"><div className="spinner" /></div>;
    if (!payslip) return <div className="module-container"><BackButton /><p>{t('common.not_found')}</p></div>;

    return (
        <div className="module-container">
            <div className="module-header">
                <BackButton />
                <h1>{t('self_service.payslip_detail')}</h1>
            </div>

            <div className="card" style={{ maxWidth: 600 }}>
                <div style={{ marginBottom: 16 }}>
                    <strong>{payslip.employee_name}</strong>
                    <span className="text-muted" style={{ marginInlineStart: 12 }}>{payslip.period_name || `${payslip.month}/${payslip.year}`}</span>
                </div>

                <table className="data-table">
                    <tbody>
                        <tr><td>{t('self_service.basic_salary')}</td><td>{fmt(payslip.basic_salary)} {currency}</td></tr>
                        <tr><td>{t('self_service.housing_allowance')}</td><td>{fmt(payslip.housing_allowance)} {currency}</td></tr>
                        <tr><td>{t('self_service.transport_allowance')}</td><td>{fmt(payslip.transport_allowance)} {currency}</td></tr>
                        <tr><td>{t('self_service.other_allowances')}</td><td>{fmt(payslip.other_allowances)} {currency}</td></tr>
                        <tr style={{ fontWeight: 600 }}><td>{t('self_service.total_earnings')}</td><td className="text-success">{fmt(payslip.total_earnings)} {currency}</td></tr>
                        <tr style={{ fontWeight: 600 }}><td>{t('self_service.total_deductions')}</td><td className="text-danger">{fmt(payslip.total_deductions)} {currency}</td></tr>
                        <tr style={{ fontWeight: 700, fontSize: '1.1em' }}><td>{t('self_service.net_salary')}</td><td>{fmt(payslip.net_salary)} {currency}</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default PayslipDetail;
