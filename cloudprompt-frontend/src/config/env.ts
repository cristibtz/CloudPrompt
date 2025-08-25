// Environment configuration and validation

interface Config {
  apiBaseUrl: string
  apiTimeout: number
  appName: string
  appVersion: string
  debugMode: boolean
  keycloak: {
    url: string
    realm: string
    clientId: string
  }
}

// Validate required environment variables
function validateEnv(): Config {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL
  const apiTimeout = import.meta.env.VITE_API_TIMEOUT
  const appName = import.meta.env.VITE_APP_NAME
  const appVersion = import.meta.env.VITE_APP_VERSION
  const debugMode = import.meta.env.VITE_DEBUG_MODE === 'true'
  
  // Keycloak configuration
  const keycloakUrl = import.meta.env.VITE_KEYCLOAK_URL
  const keycloakRealm = import.meta.env.VITE_KEYCLOAK_REALM
  const keycloakClientId = import.meta.env.VITE_KEYCLOAK_CLIENT_ID

  if (!apiBaseUrl) {
    throw new Error('VITE_API_BASE_URL is required in environment variables')
  }

  return {
    apiBaseUrl,
    apiTimeout: apiTimeout ? parseInt(apiTimeout, 10) : 30000,
    appName: appName || 'CloudPrompt',
    appVersion: appVersion || '0.0.2',
    debugMode,
    keycloak: {
      url: keycloakUrl || 'http://192.168.100.11:8080',
      realm: keycloakRealm || 'cloudprompt',
      clientId: keycloakClientId || 'cloudprompt-client',
    },
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
    keycloak: config.keycloak,
  })
}
