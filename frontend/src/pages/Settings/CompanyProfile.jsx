import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { companiesAPI } from '../../utils/api';
import { getCompanyId } from '../../utils/auth';
import {
    Building2, Mail, Phone, MapPin, Hash, Globe,
    Calendar, ShieldCheck, CreditCard, Camera
} from 'lucide-react';
import BackButton from '../../components/common/BackButton';

const CompanyProfile = () => {
    const { t, i18n } = useTranslation();
    const [company, setCompany] = useState(null);
    const [loading, setLoading] = useState(true);
    const companyId = getCompanyId();
    const isRTL = i18n.dir() === 'rtl';

    useEffect(() => {
        const fetchCompany = async () => {
            try {
                const res = await companiesAPI.getCurrentCompany(companyId);
                setCompany(res.data);
            } catch (err) {
                console.error("Failed to fetch company profile", err);
            } finally {
                setLoading(false);
            }
        };
        if (companyId) fetchCompany();
    }, [companyId]);

    if (loading) return <div className="page-center"><span className="loading"></span></div>;
    if (!company) return <div className="p-10 text-center"><h2>{t('common.error_loading_data')}</h2></div>;

    const details = [
        { label: t('auth.company_name'), value: company.company_name, icon: Building2 },
        { label: t('auth.company_name_en'), value: company.company_name_en, icon: Globe },
        { label: t('auth.email'), value: company.email, icon: Mail },
        { label: t('auth.phone'), value: company.phone || t('common.not_set'), icon: Phone },
        { label: t('auth.address'), value: company.address || t('common.not_set'), icon: MapPin },
        { label: t('auth.tax_number'), value: company.tax_number || t('common.not_set'), icon: Hash },
        { label: t('auth.cr_number') || 'رقم السجل التجاري', value: company.cr_number || company.id, icon: ShieldCheck },
        { label: t('auth.company_id'), value: company.id, icon: ShieldCheck, mono: true },
        { label: t('auth.currency'), value: company.currency, icon: CreditCard },
        { label: t('auth.plan_type'), value: company.plan_type || 'Basic', icon: ShieldCheck },
        { label: t('common.created_at'), value: new Date(company.created_at).toLocaleDateString(i18n.language), icon: Calendar },
    ];

    return (
        <div className="workspace fade-in">
            <div className="workspace-header mb-8">
                <div className="d-flex align-items-center gap-3">
                    <BackButton />
                    <div>
                        <h1 className="workspace-title">{t('nav.company_profile') || 'ملف الشركة'}</h1>
                        <p className="workspace-subtitle">{t('settings.company.subtitle')}</p>
                    </div>
                </div>
            </div>

            <div className="row g-4">
                {/* Logo Card */}
                <div className="col-md-4">
                    <div className="card h-100">
                        <div className="card-body text-center p-5">
                            <div className="mx-auto mb-4 relative group" style={{ width: '150px', height: '150px' }}>
                                <div className="w-100 h-100 rounded-circle bg-light border-2 border-dashed d-flex align-items-center justify-content-center overflow-hidden">
                                    {company.logo_url ? (
                                        <img
                                            src={`${import.meta.env.VITE_API_URL}${company.logo_url}`}
                                            alt="Logo"
                                            className="w-100 h-100 object-fit-contain"
                                        />
                                    ) : (
                                        <Building2 size={60} className="text-muted" />
                                    )}
                                </div>
                            </div>
                            <h2 className="h4 fw-bold">{company.company_name}</h2>
                            <p className="text-secondary">{company.email}</p>
                            <span className={`badge ${company.status === 'active' ? 'bg-success-subtle text-success' : 'bg-warning-subtle text-warning'} px-3 py-2 rounded-pill`}>
                                {company.status || 'Active'}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Info Card */}
                <div className="col-md-8">
                    <div className="card">
                        <div >
                            <h3 className="h5 fw-bold mb-4 border-bottom pb-3">{t('auth.company_info')}</h3>
                            <div className="row g-4">
                                {details.map((item, idx) => (
                                    <div key={idx} className="col-md-6">
                                        <div className="d-flex align-items-start gap-3">
                                            <div className="p-2 bg-primary-subtle text-primary rounded-3">
                                                <item.icon size={20} />
                                            </div>
                                            <div>
                                                <label className="small text-secondary fw-bold d-block mb-1">{item.label}</label>
                                                <div className={`fw-semibold ${item.mono ? 'font-monospace' : ''}`}>{item.value}</div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CompanyProfile;
