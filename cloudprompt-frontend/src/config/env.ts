// Environment configuration with validation
interface Config {
  apiBaseUrl: string
  apiTimeout: number
  appName: string
  appVersion: string
  debugMode: boolean
}

// Validate required environment variables
function validateEnv(): Config {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL
  const apiTimeout = import.meta.env.VITE_API_TIMEOUT
  const appName = import.meta.env.VITE_APP_NAME
  const appVersion = import.meta.env.VITE_APP_VERSION
  const debugMode = import.meta.env.VITE_DEBUG_MODE === 'true'

  if (!apiBaseUrl) {
    throw new Error('VITE_API_BASE_URL is required in environment variables')
  }

  return {
    apiBaseUrl,
    apiTimeout: apiTimeout ? parseInt(apiTimeout, 10) : 30000,
    appName: appName || 'CloudPrompt',
    appVersion: appVersion || '0.0.1',
    debugMode,
  }
}

export const config = validateEnv()

// Development helper to log configuration
if (config.debugMode) {
  console.log('🔧 App Configuration:', {
    apiBaseUrl: config.apiBaseUrl,
    apiTimeout: config.apiTimeout,
    appName: config.appName,
    appVersion: config.appVersion,
  })
}
