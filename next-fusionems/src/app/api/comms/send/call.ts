import { jsonResponse, parseJson, requireEnv } from '../shared'

type CallPayload = {
  to: string
  from?: string
  threadId?: string
}

export async function handleCall(request: Request): Promise<Response> {
  const payload = await parseJson<CallPayload>(request)
  if (!payload.to) {
    return jsonResponse({ error: 'Missing call recipient' }, 400)
  }
  const apiKey = requireEnv('TELNYX_API_KEY')
  const fromNumber = payload.from || requireEnv('TELNYX_CALLER_ID')
  const connectionId = requireEnv('TELNYX_CONNECTION_ID')
  const response = await fetch('https://api.telnyx.com/v2/calls', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      connection_id: connectionId,
      to: payload.to,
      from: fromNumber,
    }),
  })
  if (!response.ok) {
    const error = await response.text()
    return jsonResponse({ error: 'Telnyx call failed', detail: error }, 502)
  }
  const result = await response.json()
  return jsonResponse({ status: 'initiated', provider: 'telnyx', result })
}
