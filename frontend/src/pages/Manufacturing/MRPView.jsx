import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { AlertCircle, ShoppingCart, CheckCircle } from 'lucide-react'
import api from '../../utils/api'
import { toastEmitter } from '../../utils/toastEmitter'
import { formatNumber } from '../../utils/format'
import { useToast } from '../../context/ToastContext'
import '../../components/ModuleStyles.css'
import BackButton from '../../components/common/BackButton';
import { PageLoading } from '../../components/common/LoadingStates'

export default function MRPView() {
    const { t, i18n } = useTranslation()
    const { id } = useParams()
    const { showToast } = useToast()

    const [mrp, setMrp] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (id) fetchMRP()
    }, [id])

    const fetchMRP = async () => {
        try {
            setLoading(true)
            const res = await api.get(`/manufacturing/mrp/calculate/${id}`)
            setMrp(res.data)
        } catch (err) {
            toastEmitter.emit(t('common.error'), 'error')
            showToast(t('manufacturing.mrp.load_error'), 'error')
        } finally {
            setLoading(false)
        }
    }

    if (loading) return <PageLoading />

    if (!mrp) return <div className="workspace p-5 text-center"><h3>{t('manufacturing.mrp.not_found')}</h3></div>

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div className="d-flex align-items-center gap-3">
                        <BackButton />
                    <div>
                        <h1 className="workspace-title">{t('manufacturing.mrp.title')}</h1>
                        <p className="text-muted small">{mrp.plan_name}</p>
                    </div>
                </div>
            </div>

            <div className="card card-flush">
                <div className="table-responsive">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>{t('manufacturing.material_name')}</th>
                                <th className="text-center">{t('manufacturing.mrp.required')}</th>
                                <th className="text-center">{t('manufacturing.mrp.on_hand')}</th>
                                <th className="text-center">{t('manufacturing.mrp.shortage')}</th>
                                <th className="text-center">{t('manufacturing.mrp.action')}</th>
                                <th className="text-center">{t('common.status_title')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {mrp.items.map((item, idx) => (
                                <tr key={idx}>
                                    <td className="fw-bold">{item.product_name}</td>
                                    <td className="text-center">{formatNumber(item.required_quantity)}</td>
                                    <td className="text-center">{formatNumber(item.on_hand_quantity)}</td>
                                    <td className="text-center">
                                        <span className={item.shortage_quantity > 0 ? 'text-danger fw-bold' : 'text-success'}>
                                            {formatNumber(item.shortage_quantity)}
                                        </span>
                                    </td>
                                    <td className="text-center">
                                        {item.suggested_action === 'purchase_order' ? (
                                            <span className="badge bg-warning-subtle text-warning d-inline-flex align-items-center gap-1">
                                                <ShoppingCart size={12} /> {t('manufacturing.mrp.create_po')}
                                            </span>
                                        ) : (
                                            <span className="badge bg-success-subtle text-success">
                                                {t('manufacturing.mrp.stock_available')}
                                            </span>
                                        )}
                                    </td>
                                    <td className="text-center">
                                        {item.shortage_quantity > 0 ? (
                                            <AlertCircle size={18} className="text-danger" />
                                        ) : (
                                            <CheckCircle size={18} className="text-success" />
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="mt-4 d-flex justify-content-end gap-2">
                <button className="btn btn-outline-primary" onClick={() => window.print()}>
                    {t('common.print')}
                </button>
                {mrp.items.some(i => i.shortage_quantity > 0) && (
                    <button className="btn btn-primary">
                        {t('manufacturing.mrp.generate_all_pos')}
                    </button>
                )}
            </div>
        </div>
    )
}
