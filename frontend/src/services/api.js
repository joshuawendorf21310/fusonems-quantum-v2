import axios from 'axios'
import { pushError } from './errorBus.js'

const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export const apiClient = axios.create({
  baseURL: baseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
  timeout: 10000,
})

apiClient.interceptors.request.use((config) => {
  const csrfToken = document.cookie
    .split('; ')
    .find((row) => row.startsWith('csrf_token='))
    ?.split('=')[1]
  if (csrfToken) {
    config.headers['X-CSRF-Token'] = csrfToken
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error?.config || {}
    const method = (config.method || 'get').toLowerCase()
    if (!error.response && method === 'get' && !config.__retried) {
      config.__retried = true
      return apiClient.request(config)
    }
    const status = error?.response?.status
    if (status === 401) {
      pushError('Session expired. Please sign in again.', status)
      if (window.location.pathname !== '/login') {
        window.location.assign('/login')
      }
    } else if (status === 403) {
      pushError('You do not have permission for that action.', status)
    } else if (status >= 500) {
      pushError('Server error. Please retry in a moment.', status)
    } else {
      pushError('Request failed. Please verify the form and try again.', status)
    }
    return Promise.reject(error)
  }
)

export async function apiFetch(path, options = {}) {
  const response = await apiClient.request({
    url: path,
    method: options.method || 'GET',
    data: options.body ? JSON.parse(options.body) : undefined,
    headers: options.headers,
  })

  return response.data
}
