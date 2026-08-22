import axios, { type AxiosResponse } from 'axios'
import type { Paginated } from '../api/types'

const ACCESS_TOKEN_KEY = 'metam.access_token'
const REFRESH_TOKEN_KEY = 'metam.refresh_token'

export const tokenStorage = {
  getAccessToken: () => localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefreshToken: () => localStorage.getItem(REFRESH_TOKEN_KEY),
  setTokens: (accessToken: string, refreshToken: string) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  },
  clear: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },
}

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000',
})

// Backend list endpoints return the raw array with the total count on the
// X-Total-Count header rather than a wrapper object, so this pairs the two
// back up into a shape the frontend can page through.
export function toPaginated<T>(response: AxiosResponse<T[]>): Paginated<T> {
  return {
    items: response.data,
    total: Number(response.headers['x-total-count'] ?? response.data.length),
  }
}

// Downloads a file from any endpoint that sets Content-Disposition (CSV
// exports, attachment downloads, ...) and saves it, reusing the same
// authenticated apiClient instance (and its token-refresh interceptor) rather
// than a bare fetch/anchor-href request.
export async function downloadFile(url: string, params?: Record<string, string | undefined>): Promise<void> {
  const response = await apiClient.get<Blob>(url, { params, responseType: 'blob' })
  const disposition = response.headers['content-disposition'] as string | undefined
  const filename = disposition?.match(/filename="?([^"]+)"?/)?.[1] ?? 'download'

  const blobUrl = URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = blobUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(blobUrl)
}

apiClient.interceptors.request.use((config) => {
  const token = tokenStorage.getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let refreshPromise: Promise<string> | null = null

async function refreshAccessToken(): Promise<string> {
  const refreshToken = tokenStorage.getRefreshToken()
  if (!refreshToken) {
    throw new Error('No refresh token available')
  }
  const response = await axios.post(
    `${apiClient.defaults.baseURL}/api/auth/refresh`,
    { refresh_token: refreshToken },
  )
  const { access_token, refresh_token } = response.data
  tokenStorage.setTokens(access_token, refresh_token)
  return access_token
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry && tokenStorage.getRefreshToken()) {
      originalRequest._retry = true
      try {
        refreshPromise ??= refreshAccessToken().finally(() => {
          refreshPromise = null
        })
        const newAccessToken = await refreshPromise
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        return apiClient(originalRequest)
      } catch {
        tokenStorage.clear()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)
