import axios from 'axios'
import { config } from '@/config/env'

interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: {
    code: string
    message: string
  }
}

const apiClient = axios.create({
  baseURL: `${config.apiBaseUrl}/api/v1`,
  timeout: config.apiTimeout,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const api = {
  executeCommand: async (prompt: string, provider: string, credentialsName: string, token?: string) => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    const requestBody = { 
      prompt, 
      provider,
      credentials_name: credentialsName
    }
    
    try {
      const response = await apiClient.post('/execute', requestBody, {
        headers
      })
      
      const result: ApiResponse = response.data
      if (!result.success) {
        throw new Error(result.error?.message || 'Command execution failed')
      }
      
      return result.data
    } catch (error: any) {
      // Handle HTTP error responses (400, 500, etc.)
      if (error.response?.data?.detail?.error?.message) {
        throw new Error(error.response.data.detail.error.message)
      } else if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail)
      } else if (error.response?.data?.error?.message) {
        throw new Error(error.response.data.error.message)
      } else if (error.message) {
        throw new Error(error.message)
      } else {
        throw new Error('Command execution failed')
      }
    }
  },

  addCredentials: async (credentialData: { provider: string, name: string, data: Record<string, string> }, token?: string) => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    try {
      const response = await apiClient.post('/credentials', credentialData, {
        headers
      })
      
      const result: ApiResponse = response.data
      if (!result.success) {
        throw new Error(result.error?.message || 'Failed to add credentials')
      }
      
      return result
    } catch (error: any) {
      // Handle HTTP error responses (400, 500, etc.)
      if (error.response?.data?.detail?.error?.message) {
        throw new Error(error.response.data.detail.error.message)
      } else if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail)
      } else if (error.response?.data?.error?.message) {
        throw new Error(error.response.data.error.message)
      } else if (error.message) {
        throw new Error(error.message)
      } else {
        throw new Error('Failed to add credentials')
      }
    }
  },

  getUserCredentials: async (token?: string) => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    try {
      const response = await apiClient.get('/credentials/user', {
        headers
      })
      
      const result: ApiResponse = response.data
      if (!result.success) {
        throw new Error(result.error?.message || 'Failed to get credentials')
      }
      
      return result.data
    } catch (error: any) {
      // Handle HTTP error responses (400, 500, etc.)
      if (error.response?.data?.detail?.error?.message) {
        throw new Error(error.response.data.detail.error.message)
      } else if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail)
      } else if (error.response?.data?.error?.message) {
        throw new Error(error.response.data.error.message)
      } else if (error.message) {
        throw new Error(error.message)
      } else {
        throw new Error('Failed to get credentials')
      }
    }
  },

  deleteCredential: async (credentialId: number, token?: string) => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    try {
      const response = await apiClient.delete(`/credentials/${credentialId}`, {
        headers
      })
      
      const result: ApiResponse = response.data
      if (!result.success) {
        throw new Error(result.error?.message || 'Failed to delete credential')
      }
      
      return result
    } catch (error: any) {
      // Handle HTTP error responses (400, 500, etc.)
      if (error.response?.data?.detail?.error?.message) {
        throw new Error(error.response.data.detail.error.message)
      } else if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail)
      } else if (error.response?.data?.error?.message) {
        throw new Error(error.response.data.error.message)
      } else if (error.message) {
        throw new Error(error.message)
      } else {
        throw new Error('Failed to delete credential')
      }
    }
  }
}
