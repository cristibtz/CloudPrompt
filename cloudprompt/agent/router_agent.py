
from cloudprompt.agent.agent import run_aws_agent, run_azure_agent, run_gcp_agent, run_proxmox_agent

async def execute_provider(provider: str, user_input: str, credentials: dict = None, keycloak_id: str = None):
    """Execute the correct agent based on the provider string."""
    if provider == "aws":
        return await run_aws_agent(user_input, credentials, keycloak_id=keycloak_id)
    elif provider == "azure":
        return await run_azure_agent(user_input, credentials, keycloak_id=keycloak_id)
    elif provider == "gcp":
        return await run_gcp_agent(user_input, credentials, keycloak_id=keycloak_id)
    elif provider == "proxmox":
        return await run_proxmox_agent(user_input, credentials, keycloak_id=keycloak_id)
    else:
        error_msg = (
            f"Unknown provider: '{provider}'. "
            "Please select a valid cloud provider (AWS, Azure, GCP, or Proxmox)."
        )
        return type('Result', (), {'output': error_msg})()