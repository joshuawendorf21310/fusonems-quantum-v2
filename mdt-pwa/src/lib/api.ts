import axios from 'axios'
import { ssoAuth } from './auth'
import { queueRequest } from './offline-queue'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000/api/v1'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  // Try SSO token first
  const ssoToken = ssoAuth.getAccessToken()
  if (ssoToken) {
    config.headers.Authorization = `Bearer ${ssoToken}`
    return config
  }
  
  // Fall back to legacy token
  try {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  } catch (error) {
    console.error('Error accessing localStorage:', error)
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      // Try to refresh SSO token
      if (ssoAuth.isAuthenticated()) {
        try {
          await ssoAuth.refresh()
          const token = ssoAuth.getAccessToken()
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        } catch (refreshError) {
          ssoAuth.logout()
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      }
    }
    
    // Queue failed non-GET requests when offline or network error
    if (
      originalRequest &&
      originalRequest.method !== 'get' &&
      (!navigator.onLine || error.code === 'ERR_NETWORK' || error.message === 'Network Error')
    ) {
      try {
        await queueRequest(
          originalRequest.url || '',
          originalRequest.method || 'POST',
          originalRequest.headers as Record<string, string>,
          originalRequest.data
        )
      } catch (queueError) {
        console.error('Failed to queue request:', queueError)
      }
    }
    
    return Promise.reject(error)
  }
)

export const getIncident = async (incidentId: string) => {
  const response = await api.get(`/incidents/${incidentId}`)
  return response.data
}

export const getTimeline = async (incidentId: string) => {
  const response = await api.get(`/timeline/${incidentId}/timeline`)
  return response.data
}

export const updateStatus = async (incidentId: string, status: string) => {
  const response = await api.post(`/timeline/${incidentId}/status`, { status })
  return response.data
}

export const updateUnitStatus = async (status: string, latitude?: number, longitude?: number) => {
  let unitId: string | null = null
  try {
    unitId = localStorage.getItem('unit_id')
  } catch (error) {
    console.error('Error accessing localStorage:', error)
    throw new Error('Failed to access unit ID')
  }
  if (!unitId) throw new Error('No unit ID found')
  
  const response = await api.patch(`/cad/units/${unitId}/status`, {
    status,
    latitude,
    longitude,
  })
  return response.data
}

export default api
