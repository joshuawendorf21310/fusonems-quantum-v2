import { apiFetch } from '../../services/api.js'

type CommsAuditPayload = {
  action: string
  entityType: 'comm_thread' | 'comm_message' | 'comm_attachment' | 'comm_event'
  entityId: string
  metadata?: Record<string, unknown>
}

export async function logCommsAudit(payload: CommsAuditPayload): Promise<void> {
  await apiFetch('/api/comms/audit', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
