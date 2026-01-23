import { randomUUID } from "crypto"

export type CommsChannel = "email" | "sms" | "fax" | "voice"
export type QueueStatus = "pending" | "sent" | "failed"

export type QueueItem = {
  id: string
  channel: CommsChannel
  status: QueueStatus
  payload: Record<string, unknown>
  error?: string
  createdAt: string
  updatedAt: string
}

export type CommsMessage = {
  id: string
  direction: "outbound" | "inbound"
  body: string
  status: string
  timestamp: string
  metadata?: Record<string, unknown>
}

export type Escalation = {
  id: string
  reason: string
  user?: string
  createdAt: string
}

export type CommsThread = {
  id: string
  channel: CommsChannel
  title: string
  participants: string[]
  status: string
  createdAt: string
  updatedAt: string
  messages: CommsMessage[]
  escalations: Escalation[]
}

const queueItems: QueueItem[] = []
const threads: Record<string, CommsThread> = {}

function now() {
  return new Date().toISOString()
}

export function addQueueItem(data: Omit<QueueItem, "id" | "status" | "createdAt" | "updatedAt"> & { status?: QueueStatus }) {
  const item: QueueItem = {
    id: randomUUID(),
    channel: data.channel,
    status: data.status ?? "pending",
    payload: data.payload,
    error: data.error,
    createdAt: now(),
    updatedAt: now(),
  }
  queueItems.unshift(item)
  return item
}

export function getQueueItems() {
  return [...queueItems]
}

export function findQueueItem(id: string) {
  return queueItems.find((item) => item.id === id)
}

export function updateQueueItem(id: string, props: Partial<Pick<QueueItem, "status" | "error">>) {
  const item = findQueueItem(id)
  if (!item) {
    return null
  }
  if (props.status) {
    item.status = props.status
  }
  if (props.error !== undefined) {
    item.error = props.error
  }
  item.updatedAt = now()
  return item
}

export function clearQueue() {
  queueItems.splice(0, queueItems.length)
}

export function createThread(params: {
  channel: CommsChannel
  title: string
  participants: string[]
  initialMessage?: Omit<CommsMessage, "id" | "timestamp">
}) {
  const id = randomUUID()
  const thread: CommsThread = {
    id,
    channel: params.channel,
    title: params.title,
    participants: params.participants,
    status: "active",
    createdAt: now(),
    updatedAt: now(),
    messages: [],
    escalations: [],
  }
  if (params.initialMessage) {
    thread.messages.push({
      id: randomUUID(),
      timestamp: now(),
      ...params.initialMessage,
    })
  }
  threads[id] = thread
  return thread
}

export function addThreadMessage(threadId: string, message: Omit<CommsMessage, "id" | "timestamp">) {
  const thread = threads[threadId]
  if (!thread) {
    return null
  }
  const newMessage: CommsMessage = {
    id: randomUUID(),
    timestamp: now(),
    ...message,
  }
  thread.messages.push(newMessage)
  thread.updatedAt = now()
  return newMessage
}

export function getThread(threadId: string) {
  return threads[threadId] ?? null
}

export function listThreads() {
  return Object.values(threads)
}

export function addEscalation(threadId: string, reason: string, user?: string) {
  const thread = threads[threadId]
  if (!thread) {
    return null
  }
  const escalation: Escalation = {
    id: randomUUID(),
    reason,
    user,
    createdAt: now(),
  }
  thread.escalations.push(escalation)
  thread.updatedAt = now()
  return escalation
}
