import { CommsSearchFilters, CommsThread } from '../../lib/comms/types'
import { listThreads } from './api'

type Subscription = {
  stop: () => void
}

export function subscribeToThreads(
  filters: CommsSearchFilters,
  onUpdate: (threads: CommsThread[]) => void,
  intervalMs = 15000
): Subscription {
  let active = true
  const poll = async () => {
    if (!active) return
    try {
      const threads = await listThreads(filters)
      if (active) {
        onUpdate(threads)
      }
    } catch (error) {
      if (active) {
        console.warn('Unable to refresh threads', error)
      }
    }
  }
  const timer = window.setInterval(poll, intervalMs)
  poll()
  return {
    stop: () => {
      active = false
      window.clearInterval(timer)
    },
  }
}
