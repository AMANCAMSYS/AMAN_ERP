import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { selfServiceAPI } from '../../utils/api';
import { FileText, Eye } from 'lucide-react';
import BackButton from '../../components/common/BackButton';
import '../../components/ModuleStyles.css';

const PayslipList = () => {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const [payslips, setPayslips] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchPayslips();
    }, []);

    const fetchPayslips = async () => {
        setLoading(true);
        try {
            const res = await selfServiceAPI.listPayslips();
            setPayslips(res.data?.data || []);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="module-loading"><div className="spinner" /></div>;

    return (
        <div className="module-container">
            <div className="module-header">
                <BackButton />
                <h1><FileText size={22} /> {t('self_service.payslips_title')}</h1>
            </div>

            {payslips.length === 0 ? (
                <div className="card"><p className="text-muted">{t('self_service.no_payslips')}</p></div>
            ) : (
                <div className="card">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>{t('self_service.period')}</th>
                                <th>{t('self_service.basic_salary')}</th>
                                <th>{t('self_service.total_earnings')}</th>
                                <th>{t('self_service.total_deductions')}</th>
                                <th>{t('self_service.net_salary')}</th>
                                <th>{t('self_service.status')}</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {payslips.map(ps => (
                                <tr key={ps.id}>
                                    <td>{ps.period_name || `${ps.month}/${ps.year}`}</td>
                                    <td>{Number(ps.basic_salary || 0).toLocaleString()}</td>
                                    <td>{Number(ps.total_earnings || 0).toLocaleString()}</td>
                                    <td>{Number(ps.total_deductions || 0).toLocaleString()}</td>
                                    <td><strong>{Number(ps.net_salary || 0).toLocaleString()}</strong></td>
                                    <td>{ps.status}</td>
                                    <td>
                                        <button className="btn btn-sm btn-secondary" onClick={() => navigate(`/hr/self-service/payslips/${ps.id}`)}>
                                            <Eye size={14} />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

export default PayslipList;
