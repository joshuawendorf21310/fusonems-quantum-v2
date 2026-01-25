import { useEffect, useState } from 'react'
import { apiFetch } from '../../services/api.js'

type AuditEvent = {
  id: string
  action: string
  entityType: string
  entityId: string
  timestamp: string | null
  metadata?: Record<string, unknown>
}

type TimelineProps = {
  callId: number | null
}

export default function Timeline({ callId }: TimelineProps) {
  const [events, setEvents] = useState<AuditEvent[]>([])
  const [status, setStatus] = useState<'idle' | 'loading' | 'error'>('idle')

  useEffect(() => {
    let isActive = true
    const fetchEvents = async () => {
      if (!callId) {
        setEvents([])
        return
      }
      setStatus('loading')
      try {
        const data = (await apiFetch('/audit')) as AuditEvent[]
        if (isActive) {
          const filtered = data.filter(
            (event) => event.entityType === 'cad_call' && event.entityId === String(callId)
          )
          setEvents(filtered)
          setStatus('idle')
        }
      } catch (error) {
        if (isActive) {
          setStatus('error')
        }
      }
    }
    fetchEvents()
    return () => {
      isActive = false
    }
  }, [callId])

  return (
    <div className="panel cad-panel cad-timeline">
      <div className="cad-panel-header">
        <div>
          <p className="panel-eyebrow">Audit Timeline</p>
          <h3>Latest Activity</h3>
        </div>
      </div>
      {!callId && <p className="empty-state">Select a call to view audit activity.</p>}
      {status === 'loading' && <p className="empty-state">Loading timeline…</p>}
      {status === 'error' && <p className="empty-state">Unable to load audit events.</p>}
      {status === 'idle' && callId && (
        <ul className="cad-timeline-list">
          {events.map((event) => (
            <li key={event.id}>
              <span className="cad-timeline-time">{event.timestamp ?? 'Unknown time'}</span>
              <span className="cad-timeline-action">{event.action}</span>
            </li>
          ))}
          {!events.length && <li className="empty-state">No audit entries for this call yet.</li>}
        </ul>
      )}
    </div>
  )
}
