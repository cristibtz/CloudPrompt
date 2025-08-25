import Keycloak from 'keycloak-js';
import { config } from '../config/env';

// Keycloak configuration
const keycloakConfig = {
  url: config.keycloak.url,
  realm: config.keycloak.realm,
  clientId: config.keycloak.clientId,
};

// Initialize Keycloak instance
const keycloak = new Keycloak(keycloakConfig);

export default keycloak;
