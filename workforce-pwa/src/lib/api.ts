import { useAuth } from './auth'
import { queueRequest } from './offline-queue'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const { token } = useAuth.getState()
  const url = `${API_URL}${endpoint}`
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string> || {})
  }
  
  try {
    const res = await fetch(url, {
      ...options,
      headers,
    })
    if (!res.ok) throw new Error(`API Error: ${res.status}`)
    return res.json()
  } catch (error) {
    // Queue failed non-GET requests when offline or network error
    const method = options.method || 'GET'
    if (
      method !== 'GET' &&
      (!navigator.onLine || error instanceof TypeError || (error as Error).message.includes('Failed to fetch'))
    ) {
      try {
        await queueRequest(
          url,
          method,
          headers,
          options.body as string
        )
      } catch (queueError) {
        console.error('Failed to queue request:', queueError)
      }
    }
    throw error
  }
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint),
  post: <T>(endpoint: string, data: unknown) => request<T>(endpoint, { method: 'POST', body: JSON.stringify(data) }),
  put: <T>(endpoint: string, data: unknown) => request<T>(endpoint, { method: 'PUT', body: JSON.stringify(data) }),
  delete: <T>(endpoint: string) => request<T>(endpoint, { method: 'DELETE' })
}

export const hrApi = {
  getSchedule: (start: string, end: string) => api.get<any[]>(`/api/v1/hr/schedule?start=${start}&end=${end}`),
  getTimeOff: () => api.get<any[]>('/api/v1/hr/timeoff'),
  requestTimeOff: (data: any) => api.post('/api/v1/hr/timeoff', data),
  getTimesheet: (periodId: string) => api.get<any>(`/api/v1/hr/timesheet/${periodId}`),
  clockIn: () => api.post('/api/v1/hr/timesheet/clock-in', {}),
  clockOut: () => api.post('/api/v1/hr/timesheet/clock-out', {}),
  getCertifications: () => api.get<any[]>('/api/v1/hr/certifications'),
  getPayStubs: () => api.get<any[]>('/api/v1/hr/paystubs'),
  getProfile: () => api.get<any>('/api/v1/hr/profile'),
  updateProfile: (data: any) => api.put('/api/v1/hr/profile', data),
  getTeam: () => api.get<any[]>('/api/v1/hr/team'),
  swapShift: (shiftId: string, targetUserId: string) => api.post('/api/v1/hr/schedule/swap', { shiftId, targetUserId })
}
