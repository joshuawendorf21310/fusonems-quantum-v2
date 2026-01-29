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

    const authToken = localStorage.getItem("token")
    if (authToken) {
      const existingHeaders = config.headers ?? {}
      config.headers = {
        ...(existingHeaders as Record<string, unknown>),
        Authorization: `Bearer ${authToken}`,
      } as unknown as AxiosRequestHeaders
    }
    return config
  })

  type RetriableConfig = AxiosRequestConfig & { __retried?: boolean }

  apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
      const config: RetriableConfig = error?.config || {}
      const method = (config.method || "get").toString().toLowerCase()
      if (!error.response && method === "get" && !config.__retried) {
        config.__retried = true
        return apiClient.request(config)
      }
      const status = error?.response?.status
      if (status === 401) {
        pushError("Session expired. Please sign in again.", status)
        if (window.location.pathname !== "/login") {
          window.location.assign("/login")
        }
      } else if (status === 403) {
        pushError("You do not have permission for that action.", status)
      } else if (status >= 500) {
        pushError("Server error. Please retry in a moment.", status)
      } else {
        pushError("Request failed. Please verify the form and try again.", status)
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
    withCredentials,
  })

  return response.data
}
