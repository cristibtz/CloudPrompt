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
  executeCommand: async (prompt: string, provider: string) => {
    const response = await apiClient.post('/execute', { prompt, provider })
    return response.data.response
  }
}
