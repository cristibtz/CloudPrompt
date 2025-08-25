import axios from 'axios'
import { config } from '@/config/env'

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: `${config.apiBaseUrl}/api/v1`,
  timeout: config.apiTimeout,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Simple API functions
export const api = {
  // Execute command - send prompt and provider and get result
  executeCommand: async (prompt: string, provider: string, token?: string) => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    
    // Add Authorization header if token is provided
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    const response = await apiClient.post('/execute', { prompt, provider }, {
      headers
    })
    return response.data.response
  }
}
