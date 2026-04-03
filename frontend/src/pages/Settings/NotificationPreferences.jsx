/**
 * NotificationPreferences — Toggle grid: event type × channel (email / in-app / push).
 *
 * Registered in the Settings section of the router.
 */
import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { notificationsAPI } from '../../utils/api'
import DataTable from '../../components/common/DataTable'
import BackButton from '../../components/common/BackButton'

// All event types the system can send
const EVENT_TYPES = [
    'leave_approved',
    'leave_rejected',
    'invoice_held',
    'invoice_approved',
    'purchase_approved',
    'review_reminder',
    'subscription_expiring',
    'performance_review_due',
    'time_off_reminder',
    'task_assigned',
    'shipment_delayed',
    'payment_received',
    'approval_requested',
]

const CHANNELS = [
    { key: 'email_enabled', label: 'notification_preferences.channel_email' },
    { key: 'in_app_enabled', label: 'notification_preferences.channel_in_app' },
    { key: 'push_enabled', label: 'notification_preferences.channel_push' },
]

/**
 * Build a preferences map from the loaded rows.
 * Missing rows default to all-enabled (true).
 */
function buildMap(rows) {
    const map = {}
    EVENT_TYPES.forEach((evt) => {
        map[evt] = { email_enabled: true, in_app_enabled: true, push_enabled: true }
    })
    rows.forEach((r) => {
        if (map[r.event_type] !== undefined) {
            map[r.event_type] = {
                email_enabled: r.email_enabled,
                in_app_enabled: r.in_app_enabled,
                push_enabled: r.push_enabled,
            }
        }
    })
    return map
}

export default function NotificationPreferences() {
    const { t } = useTranslation()
    const [prefs, setPrefs] = useState(() => buildMap([]))
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(null) // event_type being saved

    useEffect(() => {
        notificationsAPI
            .getPreferences()
            .then((res) => setPrefs(buildMap(res.data || [])))
            .catch(() => {/* silently use defaults */})
            .finally(() => setLoading(false))
    }, [])

    const handleToggle = async (eventType, channel) => {
        const current = prefs[eventType]
        const updated = { ...current, [channel]: !current[channel] }
        // Optimistic update
        setPrefs((p) => ({ ...p, [eventType]: updated }))
        setSaving(eventType)
        try {
            await notificationsAPI.updatePreference({ event_type: eventType, ...updated })
        } catch {
            // Roll back on failure
            setPrefs((p) => ({ ...p, [eventType]: current }))
        } finally {
            setSaving(null)
        }
    }

    const tableData = EVENT_TYPES.map((evt) => ({ event_type: evt, ...prefs[evt] }))

    const columns = [
        {
            key: 'event_type',
            label: t('notification_preferences.event_type'),
            render: (val, row) => (
                <span style={{ fontWeight: 500 }}>
                    {t('notification_preferences.event_' + val)}
                    {saving === val && (
                        <span style={{ marginInlineStart: 8, fontSize: '0.7rem', color: 'var(--muted)' }}>
                            ⏳
                        </span>
                    )}
                </span>
            ),
        },
        ...CHANNELS.map((ch) => ({
            key: ch.key,
            label: t(ch.label),
            render: (val, row) => (
                <label style={{ display: 'inline-flex', alignItems: 'center', cursor: 'pointer' }}>
                    <input
                        type="checkbox"
                        checked={val ?? true}
                        onChange={() => handleToggle(row.event_type, ch.key)}
                        style={{ width: 16, height: 16, cursor: 'pointer' }}
                    />
                </label>
            ),
        })),
    ]

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <h1 className="workspace-title">{t('notification_preferences.title')}</h1>
                <p className="workspace-subtitle">{t('notification_preferences.subtitle')}</p>
            </div>

            {loading ? (
                <div style={{ padding: 40, textAlign: 'center', color: 'var(--muted)' }}>
                    {t('notification_preferences.loading')}
                </div>
            ) : (
                <div className="card" style={{ overflowX: 'auto' }}>
                    <DataTable data={tableData} columns={columns} rowKey="event_type" />
                </div>
            )}
        </div>
    )
}
