import { jsonResponse, parseJson, requireEnv } from '../shared'

type FaxPayload = {
  to: string
  documentUrl: string
  coverPage?: string
  threadId?: string
}

export async function handleFaxSend(request: Request): Promise<Response> {
  const payload = await parseJson<FaxPayload>(request)
  if (!payload.to || !payload.documentUrl) {
    return jsonResponse({ error: 'Missing required fax fields' }, 400)
  }
  const apiKey = requireEnv('TELNYX_API_KEY')
  const fromNumber = requireEnv('TELNYX_FAX_NUMBER')
  const response = await fetch('https://api.telnyx.com/v2/faxes', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      from: fromNumber,
      to: payload.to,
      media_url: payload.documentUrl,
      header: payload.coverPage,
    }),
  })
  if (!response.ok) {
    const error = await response.text()
    return jsonResponse({ error: 'Telnyx fax failed', detail: error }, 502)
  }
  const result = await response.json()
  return jsonResponse({ status: 'sent', provider: 'telnyx', result })
}
