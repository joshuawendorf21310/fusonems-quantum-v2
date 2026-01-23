const listeners = new Set()

export function pushError(message, status = null) {
  const payload = {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    message,
    status,
  }
  listeners.forEach((listener) => listener(payload))
}

export function subscribeErrors(listener) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}
