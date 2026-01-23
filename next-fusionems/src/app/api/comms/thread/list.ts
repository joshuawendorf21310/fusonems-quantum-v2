import { jsonResponse, parseJson, requireEnv } from '../shared'

export async function handleThreadList(request: Request): Promise<Response> {
  const payload = await parseJson<Record<string, unknown>>(request)
  const baseUrl = requireEnv('COMMS_CORE_URL')
  const response = await fetch(`${baseUrl}/api/comms/thread/list`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${requireEnv('COMMS_CORE_TOKEN')}`,
      'x-org-id': request.headers.get('x-org-id') ?? '',
      'x-user-id': request.headers.get('x-user-id') ?? '',
      'x-user-role': request.headers.get('x-user-role') ?? '',
    },
    body: JSON.stringify(payload),
  })
  const text = await response.text()
  if (!response.ok) {
    return jsonResponse({ error: 'Thread list failed', detail: text }, response.status)
  }
  return new Response(text, {
    status: 200,
    headers: { 'content-type': 'application/json' },
  })
}
