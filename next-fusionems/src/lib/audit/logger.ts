import { apiFetch } from '../../services/api.js'

type AuditLogInput = {
  action: string
  userId?: string
  orgId?: string
  entityType: string
  entityId: string
  before?: Record<string, unknown>
  after?: Record<string, unknown>
  timestamp?: string
  metadata?: Record<string, unknown>
}

async function log(entry: AuditLogInput): Promise<void> {
  await apiFetch('/audit/log', {
    method: 'POST',
    body: JSON.stringify({
      action: entry.action,
      entity_type: entry.entityType,
      entity_id: entry.entityId,
      before: entry.before,
      after: entry.after,
      metadata: entry.metadata,
      timestamp: entry.timestamp,
    }),
  })
}

const audit = { log }

export default audit
