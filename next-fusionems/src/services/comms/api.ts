import { apiFetch } from '../api.js'
import {
  CommsAttachment,
  CommsMessage,
  CommsSearchFilters,
  CommsThread,
} from '../../lib/comms/types'

type SendEmailPayload = {
  threadId?: string
  subject: string
  body: string
  to: string[]
  cc?: string[]
  bcc?: string[]
  attachments?: CommsAttachment[]
}

type SendSmsPayload = {
  threadId?: string
  to: string
  body: string
  mediaUrls?: string[]
}

type SendFaxPayload = {
  threadId?: string
  to: string
  documentUrl: string
  coverPage?: string
}

type InitiateCallPayload = {
  to: string
  from?: string
  threadId?: string
}

export async function listThreads(filters: CommsSearchFilters = {}): Promise<CommsThread[]> {
  return apiFetch('/api/comms/thread/list', {
    method: 'POST',
    body: JSON.stringify(filters),
  })
}

export async function listMessages(threadId: string): Promise<CommsMessage[]> {
  return apiFetch(`/api/comms/thread/${threadId}/messages`)
}

export async function sendEmail(payload: SendEmailPayload): Promise<CommsMessage> {
  return apiFetch('/api/comms/send/email', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function sendSms(payload: SendSmsPayload): Promise<CommsMessage> {
  return apiFetch('/api/comms/send/sms', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function sendFax(payload: SendFaxPayload): Promise<CommsMessage> {
  return apiFetch('/api/comms/send/fax', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function initiateCall(payload: InitiateCallPayload): Promise<{ callId: string }> {
  return apiFetch('/api/comms/send/call', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function uploadAttachment(file: File): Promise<CommsAttachment> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await fetch('/api/comms/attachments', {
    method: 'POST',
    body: formData,
    credentials: 'include',
  })
  if (!response.ok) {
    throw new Error('Attachment upload failed')
  }
  return response.json()
}

export async function markThreadRead(threadId: string): Promise<void> {
  await apiFetch(`/api/comms/thread/${threadId}/read`, {
    method: 'POST',
    body: JSON.stringify({}),
  })
}
