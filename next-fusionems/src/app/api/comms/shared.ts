import { createHmac, timingSafeEqual, createPublicKey, verify } from 'crypto'

export type CommsRequestContext = {
  orgId: string
  actorId: string
  actorRole: string
}

export function requireEnv(name: string): string {
  const value = process.env[name]
  if (!value) {
    throw new Error(`Missing required env var: ${name}`)
  }
  return value
}

export async function parseJson<T>(request: Request): Promise<T> {
  const text = await request.text()
  if (!text) {
    throw new Error('Empty request body')
  }
  return JSON.parse(text) as T
}

export function getContext(request: Request): CommsRequestContext {
  const orgId = request.headers.get('x-org-id')
  const actorId = request.headers.get('x-user-id')
  const actorRole = request.headers.get('x-user-role')
  if (!orgId || !actorId || !actorRole) {
    throw new Error('Missing org or actor context')
  }
  return { orgId, actorId, actorRole }
}

export function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'content-type': 'application/json' },
  })
}

export function verifyPostmarkSignature(body: string, signature: string, token: string): boolean {
  const hmac = createHmac('sha256', token)
  hmac.update(body)
  const digest = hmac.digest('base64')
  const expected = Buffer.from(digest)
  const provided = Buffer.from(signature)
  if (expected.length !== provided.length) {
    return false
  }
  return timingSafeEqual(expected, provided)
}

export function verifyTelnyxSignature(
  body: string,
  signature: string,
  timestamp: string,
  publicKey: string
): boolean {
  const message = `${timestamp}.${body}`
  const key = createPublicKey(publicKey)
  return verify(null, Buffer.from(message), key, Buffer.from(signature, 'base64'))
}
