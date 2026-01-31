import axios, {
  type AxiosRequestConfig,
  type AxiosRequestHeaders,
  type AxiosResponse,
} from "axios"
import { pushError } from "./errorBus"

const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? ""

export const apiClient = axios.create({
  baseURL: baseUrl,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
  timeout: 10000,
})

if (typeof window !== "undefined") {
  apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem("token")
    if (token) {
      const existingHeaders = config.headers ?? {}
      config.headers = {
        ...(existingHeaders as Record<string, unknown>),
        Authorization: `Bearer ${token}`,
      } as unknown as AxiosRequestHeaders
    }
    const csrfToken = document.cookie
      .split("; ")
      .find((row) => row.startsWith("csrf_token="))
      ?.split("=")[1]
    if (csrfToken) {
      const existingHeaders = config.headers ?? {}
      config.headers = {
        ...(existingHeaders as Record<string, unknown>),
        "X-CSRF-Token": csrfToken,
      } as unknown as AxiosRequestHeaders
    }
    return config
  })

  type RetriableConfig = AxiosRequestConfig & { 
    __retryCount?: number
    __retryDelay?: number
  }

  const MAX_RETRY_COUNT = 3
  const INITIAL_RETRY_DELAY = 1000 // 1 second
  const MAX_RETRY_DELAY = 10000 // 10 seconds

  const getRetryDelay = (retryCount: number): number => {
    // Exponential backoff: delay = INITIAL_DELAY * 2^retryCount
    const delay = INITIAL_RETRY_DELAY * Math.pow(2, retryCount)
    return Math.min(delay, MAX_RETRY_DELAY)
  }

  const shouldRetry = (error: unknown, config: RetriableConfig): boolean => {
    const retryCount = config.__retryCount ?? 0
    
    // Don't retry if we've exceeded max retries
    if (retryCount >= MAX_RETRY_COUNT) {
      return false
    }

    // Only retry on network errors or 5xx server errors
    const axiosError = error as { response?: { status?: number } }
    const status = axiosError?.response?.status
    
    // Retry on network errors (no response) or 5xx server errors
    if (!axiosError.response || (status && status >= 500 && status < 600)) {
      const method = (config.method || "get").toString().toLowerCase()
      // Only retry GET requests or idempotent methods
      return ["get", "head", "options"].includes(method)
    }

    return false
  }

  apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
      const config: RetriableConfig = error?.config || {}
      
      if (shouldRetry(error, config)) {
        const retryCount = (config.__retryCount ?? 0) + 1
        const delay = getRetryDelay(retryCount - 1)
        
        config.__retryCount = retryCount
        config.__retryDelay = delay

        // Wait before retrying
        await new Promise((resolve) => setTimeout(resolve, delay))

        return apiClient.request(config)
      }

      // Extract error message from response
      const axiosError = error as { 
        response?: { 
          status?: number
          data?: { detail?: string | Array<{ msg?: string }> }
        }
        message?: string
      }
      
      const status = axiosError?.response?.status
      let errorMessage: string

      if (status === 401) {
        errorMessage = "Session expired. Please sign in again."
        pushError(errorMessage, status)
        if (window.location.pathname !== "/login") {
          window.location.assign("/login")
        }
      } else if (status === 403) {
        errorMessage = "You do not have permission for that action."
        pushError(errorMessage, status)
      } else if (status === 404) {
        errorMessage = "The requested resource was not found."
        pushError(errorMessage, status)
      } else if (status === 422) {
        // Validation error - try to extract specific messages
        const detail = axiosError.response?.data?.detail
        if (typeof detail === "string") {
          errorMessage = detail
        } else if (Array.isArray(detail) && detail.length > 0) {
          errorMessage = detail
            .map((d) => d.msg || "Validation error")
            .filter(Boolean)
            .join(". ")
        } else {
          errorMessage = "Validation error. Please check your input."
        }
        pushError(errorMessage, status)
      } else if (status && status >= 500) {
        errorMessage = axiosError.response?.data?.detail || 
          "Server error. Please try again in a moment."
        pushError(errorMessage, status)
      } else if (!axiosError.response) {
        // Network error
        errorMessage = axiosError.message || 
          "Network error. Please check your connection and try again."
        pushError(errorMessage, 0)
      } else {
        errorMessage = axiosError.response?.data?.detail || 
          "Request failed. Please verify the form and try again."
        pushError(errorMessage, status)
      }

      return Promise.reject(error)
    }
  )
}

interface ApiFetchOptions {
  method?: AxiosRequestConfig["method"]
  body?: string
  headers?: AxiosRequestConfig["headers"]
  credentials?: RequestCredentials
  withCredentials?: boolean
}

export async function apiFetch<T = unknown>(
  path: string,
  options: ApiFetchOptions = {}
): Promise<T> {
  const withCredentials =
    options.withCredentials ?? (options.credentials ? options.credentials === "include" : undefined)
  const response: AxiosResponse<T> = await apiClient.request({
    url: path,
    method: options.method || "GET",
    data: options.body ? JSON.parse(options.body) : undefined,
    headers: options.headers,
    withCredentials:
      options.credentials === "omit"
        ? false
        : options.withCredentials ?? (options.credentials ? options.credentials === "include" : undefined),
  })

  return response.data
}
