import { useState, useEffect } from 'react'
import { backupAPI } from '../../utils/api'
import { useTranslation } from 'react-i18next'
import { formatShortDate } from '../../utils/dateUtils'
import { useToast } from '../../context/ToastContext'
import BackButton from '../../components/common/BackButton'

function BackupManagement() {
    const { t } = useTranslation()
    const { showToast } = useToast()
    const [backups, setBackups] = useState([])
    const [loading, setLoading] = useState(true)
    const [creating, setCreating] = useState(false)

    const fetchBackups = async () => {
        try { const r = await backupAPI.list(); setBackups(r.data) }
        catch { console.error }
        finally { setLoading(false) }
    }

    useEffect(() => { fetchBackups() }, [])

    const handleCreate = async () => {
        setCreating(true)
        try {
            await backupAPI.create()
            showToast(t('backup.created'), 'success')
            fetchBackups()
        } catch (err) {
            showToast(err.response?.data?.detail || t('common.error'), 'error')
        } finally { setCreating(false) }
    }

    const handleDownload = async (id) => {
        try {
            const res = await backupAPI.download(id)
            const blob = new Blob([res.data])
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `backup_${id}.dump`
            a.click()
            window.URL.revokeObjectURL(url)
        } catch (err) {
            showToast(t('common.error'), 'error')
        }
    }

    if (loading) return <div className="p-4"><span className="loading"></span></div>

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">💾 {t('backup.title')}</h1>
                    <p className="workspace-subtitle">{t('backup.subtitle')}</p>
                </div>
                <div className="header-actions">
                    <button className="btn btn-primary" onClick={handleCreate} disabled={creating}>
                        {creating ? t('backup.creating') : `+ ${t('backup.create_new')}`}
                    </button>
                </div>
            </div>

            <div className="card">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>{t('backup.filename')}</th>
                            <th>{t('backup.size')}</th>
                            <th>{t('common.date')}</th>
                            <th>{t('common.actions')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {backups.length === 0 ? (
                            <tr><td colSpan="5" className="text-center py-5 text-muted">{t('backup.empty')}</td></tr>
                        ) : backups.map(b => (
                            <tr key={b.id}>
                                <td>{b.id}</td>
                                <td className="font-medium">{b.filename}</td>
                                <td>{b.file_size ? `${(b.file_size / 1024 / 1024).toFixed(2)} MB` : '-'}</td>
                                <td>{formatShortDate(b.created_at)}</td>
                                <td>
                                    <button className="btn btn-secondary btn-sm" onClick={() => handleDownload(b.id)}>
                                        📥 {t('backup.download')}
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}

export default BackupManagement
