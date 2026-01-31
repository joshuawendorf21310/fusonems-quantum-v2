import axios from 'axios'
import type {
  CheckoutState,
  RigCheckItem,
  EquipmentItem,
  InventoryItem,
  ControlledSubstance,
  EpcrRecord,
  Patient,
  VitalSet,
  Assessment,
  Intervention,
  MedicationAdmin,
  Narrative,
} from '../types'
import { queueRequest } from './offline-queue'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  try {
    const token = localStorage.getItem('epcr_token')
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

export const auth = {
  login: (credentials: { username: string; password: string; unitId: string }) =>
    api.post<{ token: string; user: any }>('/auth/login', credentials),
  logout: () => api.post('/auth/logout'),
  refresh: () => api.post<{ token: string }>('/auth/refresh'),
}

export const checkout = {
  getRigCheckItems: (unitId: string) =>
    api.get<RigCheckItem[]>(`/epcr-tablet/checkout/rig-check/${unitId}`),
  updateRigCheckItem: (itemId: string, data: Partial<RigCheckItem>) =>
    api.patch<RigCheckItem>(`/epcr-tablet/checkout/rig-check/item/${itemId}`, data),
  completeRigCheck: (unitId: string, signature: string) =>
    api.post(`/epcr-tablet/checkout/rig-check/${unitId}/complete`, { signature }),

  getEquipmentItems: (unitId: string) =>
    api.get<EquipmentItem[]>(`/epcr-tablet/checkout/equipment/${unitId}`),
  updateEquipmentStatus: (itemId: string, status: EquipmentItem['status']) =>
    api.patch(`/epcr-tablet/checkout/equipment/item/${itemId}`, { status }),
  completeEquipmentCheck: (unitId: string) =>
    api.post(`/epcr-tablet/checkout/equipment/${unitId}/complete`),

  getInventoryItems: (unitId: string) =>
    api.get<InventoryItem[]>(`/epcr-tablet/checkout/inventory/${unitId}`),
  updateInventoryCount: (itemId: string, quantity: number, notes?: string) =>
    api.patch(`/epcr-tablet/checkout/inventory/item/${itemId}`, { quantity, notes }),
  completeInventoryCheck: (unitId: string, discrepancies: string[]) =>
    api.post(`/epcr-tablet/checkout/inventory/${unitId}/complete`, { discrepancies }),

  getControlledSubstances: (unitId: string) =>
    api.get<ControlledSubstance[]>(`/epcr-tablet/checkout/narcotics/${unitId}`),
  verifyControlledSubstance: (
    substanceId: string,
    data: { quantity: number; sealIntact: boolean; witnessName: string }
  ) => api.patch(`/epcr-tablet/checkout/narcotics/item/${substanceId}/verify`, data),
  completeNarcoticsCheck: (
    unitId: string,
    data: { primarySignature: string; witnessSignature: string; witnessName: string }
  ) => api.post(`/epcr-tablet/checkout/narcotics/${unitId}/complete`, data),

  getCheckoutState: (unitId: string, shiftId: string) =>
    api.get<CheckoutState>(`/epcr-tablet/checkout/state/${unitId}/${shiftId}`),
  submitCheckout: (state: CheckoutState) =>
    api.post('/epcr-tablet/checkout/submit', state),
}

export const epcr = {
  getRecords: (params?: { status?: string; unitId?: string; date?: string }) =>
    api.get<EpcrRecord[]>('/epcr/records', { params }),
  getRecord: (id: string) => api.get<EpcrRecord>(`/epcr/records/${id}`),
  createRecord: (data: { unitId: string; serviceType: string; crewlinkTripId?: string }) =>
    api.post<EpcrRecord>('/epcr/records', data),
  updateRecord: (id: string, data: Partial<EpcrRecord>) =>
    api.patch<EpcrRecord>(`/epcr/records/${id}`, data),

  updatePatient: (recordId: string, patient: Partial<Patient>) =>
    api.patch<Patient>(`/epcr/records/${recordId}/patient`, patient),

  getVitals: (recordId: string) => api.get<VitalSet[]>(`/epcr/records/${recordId}/vitals`),
  addVitals: (recordId: string, vitals: Omit<VitalSet, 'id' | 'recordId'>) =>
    api.post<VitalSet>(`/epcr/records/${recordId}/vitals`, vitals),
  updateVitals: (recordId: string, vitalId: string, data: Partial<VitalSet>) =>
    api.patch<VitalSet>(`/epcr/records/${recordId}/vitals/${vitalId}`, data),

  updateAssessment: (recordId: string, assessment: Partial<Assessment>) =>
    api.patch<Assessment>(`/epcr/records/${recordId}/assessment`, assessment),

  addIntervention: (recordId: string, intervention: Omit<Intervention, 'id' | 'recordId'>) =>
    api.post<Intervention>(`/epcr/records/${recordId}/interventions`, intervention),
  updateIntervention: (recordId: string, interventionId: string, data: Partial<Intervention>) =>
    api.patch<Intervention>(`/epcr/records/${recordId}/interventions/${interventionId}`, data),

  administerMedication: (recordId: string, medication: Omit<MedicationAdmin, 'id' | 'recordId'>) =>
    api.post<MedicationAdmin>(`/epcr/records/${recordId}/medications`, medication),
  administerControlled: (
    recordId: string,
    medication: Omit<MedicationAdmin, 'id' | 'recordId'> & {
      witnessName: string
      witnessSignature: string
    }
  ) => api.post<MedicationAdmin>(`/epcr/records/${recordId}/medications/controlled`, medication),
  recordWaste: (
    recordId: string,
    medicationId: string,
    data: { wasteAmount: number; wasteWitnessName: string; wasteWitnessSignature: string }
  ) => api.post(`/epcr/records/${recordId}/medications/${medicationId}/waste`, data),

  addNarrative: (recordId: string, narrative: { content: string; type: string }) =>
    api.post<Narrative>(`/epcr/records/${recordId}/narrative`, narrative),

  signRecord: (recordId: string, data: { role: string; signature: string }) =>
    api.post(`/epcr/records/${recordId}/sign`, data),
  submitRecord: (recordId: string) => api.post(`/epcr/records/${recordId}/submit`),
  lockRecord: (recordId: string) => api.post(`/epcr/records/${recordId}/lock`),
}

export const inventory = {
  useItem: (itemId: string, data: { quantity: number; recordId?: string; reason: string }) =>
    api.post(`/inventory/items/${itemId}/use`, data),
  restockItem: (itemId: string, data: { quantity: number; lotNumber: string; expiration: string }) =>
    api.post(`/inventory/items/${itemId}/restock`, data),
  getUsageHistory: (itemId: string) => api.get(`/inventory/items/${itemId}/history`),
}

export const ocr = {
  scanDevice: async (deviceType: string, imageFile: File | Blob) => {
    const formData = new FormData()
    formData.append('device_type', deviceType)
    formData.append('image', imageFile)
    return api.post('/ocr/scan_device', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  scanDeviceBase64: async (deviceType: string, imageBase64: string) => {
    // Convert base64 to blob
    const byteString = atob(imageBase64.split(',')[1])
    const mimeString = imageBase64.split(',')[0].split(':')[1].split(';')[0]
    const ab = new ArrayBuffer(byteString.length)
    const ia = new Uint8Array(ab)
    for (let i = 0; i < byteString.length; i++) {
      ia[i] = byteString.charCodeAt(i)
    }
    const blob = new Blob([ab], { type: mimeString })
    return ocr.scanDevice(deviceType, blob)
  },
}

export default api
