import { jsonResponse, parseJson, requireEnv } from '../shared'
import { CommsAttachment } from '../../../../lib/comms/types'

type EmailPayload = {
  subject: string
  body: string
  to: string[]
  cc?: string[]
  bcc?: string[]
  attachments?: CommsAttachment[]
  threadId?: string
}

export async function handleEmailSend(request: Request): Promise<Response> {
  const payload = await parseJson<EmailPayload>(request)
  if (!payload.subject || !payload.body || !payload.to?.length) {
    return jsonResponse({ error: 'Missing required email fields' }, 400)
  }
  const apiKey = requireEnv('POSTMARK_API_KEY')
  const fromAddress = requireEnv('POSTMARK_FROM_ADDRESS')
  const response = await fetch('https://api.postmarkapp.com/email', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Postmark-Server-Token': apiKey,
    },
    body: JSON.stringify({
      From: fromAddress,
      To: payload.to.join(','),
      Cc: payload.cc?.join(','),
      Bcc: payload.bcc?.join(','),
      Subject: payload.subject,
      HtmlBody: payload.body,
      Attachments: payload.attachments?.map((attachment) => ({
        Name: attachment.filename,
        ContentType: attachment.contentType,
        Content: attachment.checksum ?? '',
      })),
    }),
  })
  if (!response.ok) {
    const error = await response.text()
    return jsonResponse({ error: 'Postmark send failed', detail: error }, 502)
  }
  const result = await response.json()
  return jsonResponse({ status: 'sent', provider: 'postmark', result })
}
