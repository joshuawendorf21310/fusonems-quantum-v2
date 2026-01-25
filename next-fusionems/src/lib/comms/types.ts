export type CommsChannel = 'email' | 'sms' | 'mms' | 'voice' | 'fax' | 'secure'

export type CommsParticipant = {
  id: string
  name: string
  address: string
  role: 'sender' | 'recipient' | 'cc' | 'bcc' | 'internal'
}

export type CommsAttachment = {
  id: string
  filename: string
  contentType: string
  size: number
  url?: string
  checksum?: string
}

export type CommsMessage = {
  id: string
  threadId: string
  channel: CommsChannel
  subject?: string
  body: string
  sender: CommsParticipant
  recipients: CommsParticipant[]
  attachments: CommsAttachment[]
  status: 'queued' | 'sent' | 'delivered' | 'failed' | 'received' | 'read'
  createdAt: string
  updatedAt?: string
  metadata?: Record<string, unknown>
}

export type CommsThread = {
  id: string
  channel: CommsChannel
  subject?: string
  preview: string
  participants: CommsParticipant[]
  lastMessageAt: string
  unreadCount: number
  tags: string[]
  assignedTo?: string
  status: 'open' | 'closed' | 'pending'
}

export type CommsEvent = {
  id: string
  threadId?: string
  messageId?: string
  channel: CommsChannel
  type: string
  payload: Record<string, unknown>
  createdAt: string
}

export type CommsSearchFilters = {
  query?: string
  channel?: CommsChannel | 'all'
  status?: string
  assignedTo?: string
  tag?: string
  unreadOnly?: boolean
}
