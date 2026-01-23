import { randomUUID } from "crypto"

type AuditEvent = {
  id: string
  action: string
  targetType: string
  targetId: string
  details: Record<string, unknown>
  createdAt: string
}

const auditEvents: AuditEvent[] = []

export function audit(
  action: string,
  targetType: string,
  targetId: string | number,
  details: Record<string, unknown> = {}
) {
  const id = randomUUID()
  const event: AuditEvent = {
    id,
    action,
    targetType,
    targetId: String(targetId),
    details,
    createdAt: new Date().toISOString(),
  }
  auditEvents.unshift(event)
  return event
}

export function getAuditEvents() {
  return [...auditEvents]
}
