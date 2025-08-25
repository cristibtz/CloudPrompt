import { createContext, useContext } from 'react';

export interface KeycloakContextType {
  keycloak: any;
  authenticated: boolean;
  token: string | undefined;
  login: () => void;
  logout: () => void;
  register: () => void;
}

const KeycloakContext = createContext<KeycloakContextType | undefined>(undefined);

export const useKeycloak = (): KeycloakContextType => {
  const context = useContext(KeycloakContext);
  if (!context) {
    throw new Error('useKeycloak must be used within a KeycloakProvider');
  }
  return context;
};

export default KeycloakContext;
