import axios from 'axios'
import { ssoAuth } from './auth'
import { queueRequest } from './offline-queue'
import type { 
  TripRequest, 
  HEMSFlightRequest, 
  TripStatus, 
  CrewStatus, 
  PTTChannel, 
  TripHistoryItem, 
  DutyStatus,
  TextMessage,
  OnlineCrewMember,
  HospitalDirectory,
  ScannedDocument,
  UnableToRespondReason,
} from '../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const ssoToken = ssoAuth.getAccessToken()
  if (ssoToken) {
    config.headers.Authorization = `Bearer ${ssoToken}`
    return config
  }
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
      if (ssoAuth.isAuthenticated()) {
        try {
          await ssoAuth.refresh()
          originalRequest.headers.Authorization = `Bearer ${ssoAuth.getAccessToken()}`
          return api(originalRequest)
        } catch {
          ssoAuth.logout()
          window.location.href = '/login'
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

export const acknowledgeTrip = async (tripId: string, timestamp?: string): Promise<TripRequest> => {
  const response = await api.post(`/crewlink/trips/${tripId}/acknowledge`, {
    timestamp: timestamp || new Date().toISOString(),
  })
  return response.data
}

export const unableToRespond = async (
  tripId: string, 
  reason: UnableToRespondReason, 
  notes?: string
): Promise<void> => {
  await api.post(`/crewlink/trips/${tripId}/unable-to-respond`, {
    reason,
    notes,
    timestamp: new Date().toISOString(),
  })
}

export const recordPatientContact = async (tripId: string, timestamp?: string): Promise<TripRequest> => {
  const response = await api.post(`/crewlink/trips/${tripId}/patient-contact`, {
    timestamp: timestamp || new Date().toISOString(),
  })
  return response.data
}

export const getTrip = async (tripId: string): Promise<TripRequest | HEMSFlightRequest> => {
  const response = await api.get(`/crewlink/trips/${tripId}`)
  return response.data
}

export const getActiveTrip = async (): Promise<TripRequest | HEMSFlightRequest | null> => {
  const response = await api.get('/crewlink/trips/active')
  return response.data
}

export const updateTripStatus = async (tripId: string, status: TripStatus): Promise<TripRequest> => {
  const response = await api.post(`/crewlink/trips/${tripId}/status`, {
    status,
    timestamp: new Date().toISOString(),
  })
  return response.data
}

export const updateCrewStatus = async (status: CrewStatus): Promise<void> => {
  await api.post('/crewlink/status', { status })
}

export const getTripHistory = async (): Promise<TripHistoryItem[]> => {
  const response = await api.get('/crewlink/trips/history')
  return response.data
}

export const getDutyStatus = async (): Promise<DutyStatus> => {
  const response = await api.get('/crewlink/duty-status')
  return response.data
}

export const getPTTChannels = async (): Promise<PTTChannel[]> => {
  const response = await api.get('/crewlink/ptt/channels')
  return response.data
}

export const sendPTTMessage = async (channelId: string, audioBlob: Blob, isEmergency: boolean): Promise<void> => {
  const formData = new FormData()
  formData.append('audio', audioBlob, 'message.webm')
  formData.append('channel_id', channelId)
  formData.append('is_emergency', String(isEmergency))
  await api.post('/crewlink/ptt/send', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const getMessages = async (): Promise<TextMessage[]> => {
  const response = await api.get('/crewlink/messages')
  return response.data
}

export const sendTextMessage = async (content: string, recipientId?: string | null): Promise<void> => {
  await api.post('/crewlink/messages', { content, recipient_id: recipientId })
}

export const getOnlineCrew = async (): Promise<OnlineCrewMember[]> => {
  const response = await api.get('/crewlink/crew/online')
  return response.data
}

export const getFacilities = async (): Promise<HospitalDirectory[]> => {
  const response = await api.get('/crewlink/facilities')
  return response.data
}

export const scanDocument = async (
  imageData: string, 
  documentType: string, 
  tripId?: string | null
): Promise<ScannedDocument> => {
  const response = await api.post('/crewlink/documents/scan', {
    image_data: imageData,
    document_type: documentType,
    trip_id: tripId,
  })
  return response.data
}

export const submitDocument = async (
  documentId: string, 
  tripId?: string | null, 
  attachToEpcr?: boolean
): Promise<void> => {
  await api.post('/crewlink/documents/submit', {
    document_id: documentId,
    trip_id: tripId,
    attach_to_epcr: attachToEpcr,
  })
}

export const getWeather = async (airportCode: string): Promise<any> => {
  const response = await api.get(`/crewlink/weather?airport_code=${airportCode}`)
  return response.data
}

export const getNOTAMs = async (airportCode: string): Promise<any> => {
  const response = await api.get(`/crewlink/notams?airport_code=${airportCode}`)
  return response.data
}

export default api
