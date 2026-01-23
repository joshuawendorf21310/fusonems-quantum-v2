type ErrorPayload = {
  id: string
  message: string
  status: number | null
}

const listeners = new Set<(payload: ErrorPayload) => void>()

export function pushError(message: string, status: number | null = null) {
  const payload: ErrorPayload = {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    message,
    status,
  }
  listeners.forEach((listener) => listener(payload))
}

export function subscribeErrors(listener: (payload: ErrorPayload) => void) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}
