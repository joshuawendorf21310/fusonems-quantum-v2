import { jsonResponse, requireEnv, verifyTelnyxSignature } from '../shared'

export async function handleTelnyxWebhook(request: Request): Promise<Response> {
  const signature = request.headers.get('Telnyx-Signature-Ed25519')
  const timestamp = request.headers.get('Telnyx-Timestamp')
  const publicKey = requireEnv('TELNYX_PUBLIC_KEY')
  const body = await request.text()
  if (!signature || !timestamp || !verifyTelnyxSignature(body, signature, timestamp, publicKey)) {
    return jsonResponse({ error: 'Invalid Telnyx signature' }, 401)
  }
  const payload = JSON.parse(body) as Record<string, unknown>
  const coreUrl = requireEnv('COMMS_CORE_URL')
  const response = await fetch(`${coreUrl}/api/comms/webhooks/telnyx`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${requireEnv('COMMS_CORE_TOKEN')}`,
    },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const error = await response.text()
    return jsonResponse({ error: 'Telnyx webhook forward failed', detail: error }, response.status)
  }
  return jsonResponse({ status: 'ok' })
}
