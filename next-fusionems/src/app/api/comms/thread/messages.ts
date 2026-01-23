import { jsonResponse, requireEnv } from '../shared'

type ThreadMessageRequest = {
  threadId: string
}

export async function handleThreadMessages(request: Request, params: ThreadMessageRequest): Promise<Response> {
  const baseUrl = requireEnv('COMMS_CORE_URL')
  const response = await fetch(`${baseUrl}/api/comms/thread/${params.threadId}/messages`, {
    headers: {
      Authorization: `Bearer ${requireEnv('COMMS_CORE_TOKEN')}`,
      'x-org-id': request.headers.get('x-org-id') ?? '',
      'x-user-id': request.headers.get('x-user-id') ?? '',
      'x-user-role': request.headers.get('x-user-role') ?? '',
    },
  })
  const text = await response.text()
  if (!response.ok) {
    return jsonResponse({ error: 'Thread messages failed', detail: text }, response.status)
  }
  return new Response(text, {
    status: 200,
    headers: { 'content-type': 'application/json' },
  })
}
