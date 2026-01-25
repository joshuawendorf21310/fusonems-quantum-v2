import { jsonResponse, requireEnv, verifyPostmarkSignature } from '../shared'

export async function handlePostmarkWebhook(request: Request): Promise<Response> {
  const token = requireEnv('POSTMARK_WEBHOOK_TOKEN')
  const signature = request.headers.get('X-Postmark-Signature')
  const body = await request.text()
  if (!signature || !verifyPostmarkSignature(body, signature, token)) {
    return jsonResponse({ error: 'Invalid Postmark signature' }, 401)
  }
  const payload = JSON.parse(body) as Record<string, unknown>
  const coreUrl = requireEnv('COMMS_CORE_URL')
  const response = await fetch(`${coreUrl}/api/comms/webhooks/postmark`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${requireEnv('COMMS_CORE_TOKEN')}`,
    },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const error = await response.text()
    return jsonResponse({ error: 'Postmark webhook forward failed', detail: error }, response.status)
  }
  return jsonResponse({ status: 'ok' })
}
