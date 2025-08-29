import { useEffect, useState, useRef } from 'react';
import type { ReactNode } from 'react';
import keycloak from './keycloak';
import KeycloakContext from './KeycloakContext';
import type { KeycloakContextType } from './KeycloakContext';
import { config } from '../config/env';

interface KeycloakProviderProps {
  children: ReactNode;
}

const loadingMessages = [
  "Loading... Be patient",
  "Almost there...",
  "Hang tight, good things take time",
  "Coffee break? We're working on it...",
  "Loading magic in progress...",
  "Just a moment, please",
  "Getting things ready for you",
  "Loading... Don't go anywhere!",
  "This won't take long",
  "Patience is a virtue... Loading...",
  "Working hard or hardly working? Loading...",
  "Loading... Time for a quick stretch?",
  "Just loading some awesome stuff",
  "Loading... Almost done, promise!",
  "Hold on, we're cooking something good"
];

export const KeycloakProvider = ({ children }: KeycloakProviderProps) => {
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);
  const [loadingMessage] = useState(() => {
    // Pick a random message on component mount
    return loadingMessages[Math.floor(Math.random() * loadingMessages.length)];
  });
  const initialized = useRef(false);

  useEffect(() => {
    const initKeycloak = async () => {
      // Prevent double initialization in React StrictMode
      if (initialized.current) {
        console.log('Keycloak already initialized, skipping...');
        return;
      }
      initialized.current = true;

      console.log('Initializing Keycloak with config:', {
        url: config.keycloak.url,
        realm: config.keycloak.realm,
        clientId: config.keycloak.clientId
      });

      try {
        const authenticated = await keycloak.init({
          onLoad: 'check-sso',
          checkLoginIframe: false,
          pkceMethod: 'S256',
        });

        console.log('Keycloak initialization result:', { authenticated, token: keycloak.token });
        setAuthenticated(authenticated);
        setToken(keycloak.token);

        // Token refresh setup
        if (authenticated) {
          // Refresh token on expiration
          keycloak.onTokenExpired = () => {
            keycloak.updateToken(30).then((refreshed) => {
              if (refreshed) {
                setToken(keycloak.token);
              }
            }).catch(() => {
              console.log('Failed to refresh token');
            });
          };

          // Refresh token every 10 minutes (600 seconds)
          const refreshInterval = setInterval(() => {
            keycloak.updateToken(600).then((refreshed) => {
              if (refreshed) {
                setToken(keycloak.token);
                console.log('Token refreshed automatically');
              }
            }).catch(() => {
              console.log('Failed to refresh token automatically');
            });
          }, 600000); // 10 minutes in milliseconds

          // Cleanup interval on unmount
          return () => clearInterval(refreshInterval);
        }
      } catch (error) {
        console.error('Keycloak initialization failed:', error);
        setError(error instanceof Error ? error.message : 'Failed to initialize authentication');
      } finally {
        setLoading(false);
      }
    };

    initKeycloak();
  }, []);

  const login = () => {
    keycloak.login({
      redirectUri: window.location.origin + '/'
    });
  };

  const logout = () => {
    keycloak.logout({
      redirectUri: window.location.origin + '/'
    });
  };

  const register = () => {
    keycloak.register();
  };

  const contextValue: KeycloakContextType = {
    keycloak,
    authenticated,
    token,
    login,
    logout,
    register,
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">{loadingMessage}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-[#E3F2FD] via-white to-[#F3E5F5]">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="bg-white rounded-lg shadow-lg border border-red-200 p-8">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-red-800 mb-2">Authentication Error</h2>
            <p className="text-red-700 mb-6">{error}</p>
            <button 
              onClick={() => window.location.reload()} 
              className="bg-red-600 hover:bg-red-700 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-300 w-full"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <KeycloakContext.Provider value={contextValue}>
      {children}
    </KeycloakContext.Provider>
  );
};
