import { jsonResponse, parseJson, requireEnv } from '../shared'

type SmsPayload = {
  to: string
  body: string
  mediaUrls?: string[]
  threadId?: string
}

export async function handleSmsSend(request: Request): Promise<Response> {
  const payload = await parseJson<SmsPayload>(request)
  if (!payload.to || !payload.body) {
    return jsonResponse({ error: 'Missing required SMS fields' }, 400)
  }
  const apiKey = requireEnv('TELNYX_API_KEY')
  const fromNumber = requireEnv('TELNYX_FROM_NUMBER')
  const response = await fetch('https://api.telnyx.com/v2/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      from: fromNumber,
      to: payload.to,
      text: payload.body,
      media_urls: payload.mediaUrls,
    }),
  })
  if (!response.ok) {
    const error = await response.text()
    return jsonResponse({ error: 'Telnyx SMS failed', detail: error }, 502)
  }
  const result = await response.json()
  return jsonResponse({ status: 'sent', provider: 'telnyx', result })
}
