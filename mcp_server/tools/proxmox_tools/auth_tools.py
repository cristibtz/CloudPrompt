from proxmoxer import ProxmoxAPI
from dotenv import load_dotenv
import logging
import os
import uuid

logger = logging.getLogger("proxmox_auth_tools_mcp")

# Simple session storage: {session_id: session_data}
_proxmox_sessions = {}

def register_tools(mcp):
    
    @mcp.tool()
    async def authenticate_proxmox(
        host: str,
        username: str,
        token_name: str,
        token_value: str
    ):
        '''
        Authenticate with Proxmox and create a session for subsequent operations.
        This tool MUST be called before any other Proxmox tools.
        
        :param host: str - Proxmox host address (e.g., "192.168.100.203").
        :param username: str - Proxmox username (e.g., "user@pve").
        :param token_name: str - Proxmox API token name.
        :param token_value: str - Proxmox API token value.
        :return: Dict with authentication status, cluster info, and session_id.
        '''
        # Generate random session UUID
        session_id = str(uuid.uuid4())
        
        logger.info(f"Authenticating Proxmox session '{session_id}' for host {host}")
        
        try:
            # Create Proxmox API connection
            proxmox = ProxmoxAPI(
                host=host,
                user=username,
                token_name=token_name,
                token_value=token_value,
                verify_ssl=False
            )
            
            # Test connection by getting cluster status
            try:
                cluster_status = proxmox.cluster.status.get()
                nodes = proxmox.nodes.get()
            except Exception as test_error:
                logger.error(f"Failed to test Proxmox connection: {test_error}")
                return {
                    "status": "error",
                    "message": f"Connection test failed: {str(test_error)}"
                }
            
            # Store session for future use
            _proxmox_sessions[session_id] = {
                'proxmox': proxmox,
                'host': host,
                'username': username,
                'authenticated': True,
                'cluster_status': cluster_status,
                'nodes': nodes
            }
            
            logger.info(f"Successfully authenticated Proxmox session '{session_id}' for host {host}")
            
            return {
                "status": "authenticated",
                "session_id": session_id,
                "host": host,
                "username": username,
                "cluster_name": cluster_status[0].get('name', 'Unknown') if cluster_status else 'Unknown',
                "total_nodes": len(nodes),
                "nodes": [node['node'] for node in nodes],
                "message": f"Proxmox session '{session_id}' authenticated successfully"
            }
            
        except Exception as e:
            logger.error(f"Proxmox authentication failed: {e}")
            return {
                "status": "error",
                "message": f"Authentication failed: {str(e)}"
            }

def get_proxmox_api(session_id: str):
    '''
    Helper function to get a Proxmox API instance from an authenticated session.
    
    :param session_id: str - Session identifier from authenticate_proxmox.
    :return: ProxmoxAPI instance or None if session not found.
    '''
    if session_id not in _proxmox_sessions:
        logger.error(f"Session '{session_id}' not found. Please authenticate first.")
        return None
    
    session_info = _proxmox_sessions[session_id]
    if not session_info['authenticated']:
        logger.error(f"Session '{session_id}' is not authenticated.")
        return None
    
    return session_info['proxmox']

def get_proxmox_session_info(session_id: str):
    '''
    Helper function to get session information.
    
    :param session_id: str - Session identifier from authenticate_proxmox.
    :return: dict - Session information or None if session not found.
    '''
    if session_id not in _proxmox_sessions:
        return None
    return _proxmox_sessions[session_id]