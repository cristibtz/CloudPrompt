import { useEffect, useState, useRef } from 'react';
import type { ReactNode } from 'react';
import keycloak from './keycloak';
import KeycloakContext from './KeycloakContext';
import type { KeycloakContextType } from './KeycloakContext';
import { config } from '../config/env';

interface KeycloakProviderProps {
  children: ReactNode;
}

export const KeycloakProvider = ({ children }: KeycloakProviderProps) => {
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);
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
          keycloak.onTokenExpired = () => {
            keycloak.updateToken(30).then((refreshed) => {
              if (refreshed) {
                setToken(keycloak.token);
              }
            }).catch(() => {
              console.log('Failed to refresh token');
            });
          };
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
          <p className="mt-4 text-gray-600">Initializing authentication...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            <h2 className="font-bold">Authentication Error</h2>
            <p>{error}</p>
            <button 
              onClick={() => window.location.reload()} 
              className="mt-2 bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
            >
              Retry
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
