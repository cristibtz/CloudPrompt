import os, time, re, json
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE  
from pydantic_ai.tools import ToolDefinition
from pydantic_ai.result import RunContext
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from dotenv import load_dotenv
from typing import Union, Optional, Any, Callable
import logfire

from rich.console import Console
from .redis_session_store import RedisSessionStore

console = Console()
load_dotenv()

logfire.configure(token=os.getenv("LOGFIRE_TOKEN"), scrubbing=False)
logfire.instrument_pydantic_ai()


MODEL = os.getenv("MODEL", "gpt-5-mini")
MCP_SERVER_URL = "http://127.0.0.1:8089/sse"
server = MCPServerSSE(url=MCP_SERVER_URL)

# Initialize Redis session store with Redis URL and file fallback
SESSION_STORE = RedisSessionStore(
    redis_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    fallback_to_file=True
)

def load_user_tokens(keycloak_id: str) -> dict:
    """Load user session tokens from Redis"""
    return SESSION_STORE.load(keycloak_id)

def save_user_tokens(keycloak_id: str, tokens: dict):
    """Save user session tokens to Redis with TTL"""
    ttl = int(os.getenv('SESSION_TTL', 1800))  # 30 minutes default
    SESSION_STORE.save(keycloak_id, tokens, ttl=ttl)

def clear_user_session(keycloak_id: str):
    """Clear user session tokens"""
    SESSION_STORE.clear_session(keycloak_id)

def print_conversation_history(keycloak_id: str):
    """Print conversation history for a session"""
    session_data = SESSION_STORE.load(keycloak_id)
    conversation_history = session_data.get('conversation_history', [])
    
    if not conversation_history:
        print(f"No conversation history found for session: {keycloak_id}")
        return
    
    print(f"\n=== CONVERSATION HISTORY FOR SESSION: {keycloak_id} ===")
    print(f"Total messages: {len(conversation_history)}")
    print(f"Exchanges: {len(conversation_history) // 2}")
    
    for i in range(0, len(conversation_history), 2):
        exchange_num = (i // 2) + 1
        user_msg = conversation_history[i] if i < len(conversation_history) else "N/A"
        assistant_msg = conversation_history[i + 1] if i + 1 < len(conversation_history) else "N/A"
        
        print(f"\n--- Exchange {exchange_num} ---")
        print(f"👤 USER: {user_msg[:100]}{'...' if len(user_msg) > 100 else ''}")
        print(f"🤖 ASSISTANT: {assistant_msg[:200]}{'...' if len(assistant_msg) > 200 else ''}")
    
    print(f"\n=== END CONVERSATION HISTORY ===\n")

def extract_tokens(result: Any) -> dict:
    """Extract MCP workflow tokens from result."""
    found = {}
    # Token patterns matching the actual MCP server format with full UUIDs
    patterns = {
        'environment_token': r'\b(env_[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\b',
        'credentials_token': r'\b(creds_[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\b',
        'generated_code_token': r'\b(generated_code_[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\b',
        'explained_token': r'\b(explained_[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\b',
        'explained_deletion_token': r'\b(explained_del_[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\b',
        'security_scan_token': r'\b(sec_[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\b',
        'request_token': r'\b(req_[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\b',
    }
    
    # Get all possible text sources from the result
    text_sources = [str(result)]
    
    if hasattr(result, 'output'):
        text_sources.append(str(result.output))
    if hasattr(result, 'data'):
        text_sources.append(str(result.data))
    if hasattr(result, '_state'):
        text_sources.append(str(result._state))
        if hasattr(result._state, 'messages'):
            text_sources.append(str(result._state.messages))
        if hasattr(result._state, 'all_messages'):
            text_sources.append(str(result._state.all_messages))
    
    # Search all text sources for tokens
    for text in text_sources:
        for token_type, pattern in patterns.items():
            if token_type not in found:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # Normalize prefixed request token into request_token key
                    if token_type == 'request_token_prefixed':
                        found['request_token'] = matches[0]
                    else:
                        found[token_type] = matches[0]

        # Special handling for request_token as bare UUID inside JSON
        if 'request_token' not in found:
            m = re.search(r'"request_token"\s*:\s*"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"', text, re.IGNORECASE)
            if m:
                found['request_token'] = m.group(1)

    print(f"Extracted tokens: {found}")  # Debug output
    return found

class CloudAgentBase:
    CLOUD_TYPE = "Cloud"
    TOOL_FILTER: Callable = None

    def __init__(self):
        self.model = MODEL
        self.server = server
        self.SYSTEM_PROMPT = (
            f"You are a helpful assistant for {self.CLOUD_TYPE} management.\n"
            f"Use the provided MCP tools step by step.\n"
            f"IMPORTANT: After each major step (getting tokens, generating code, explaining, security scanning), STOP and return the result to the user for confirmation before proceeding.\n"
            f"Never automatically continue to the next step without user confirmation.\n"
        )
        
        if self.CLOUD_TYPE == "AWS":
            self.SYSTEM_PROMPT += (
                "\n=== AWS MCP WORKFLOW ===\n"
                "CRITICAL: Follow this exact pattern step-by-step with user confirmation after each step.\n"
                "\n"
                "1. AUTHENTICATION (if no credentials_token in session):\n"
                "   check_environment_variables() → environment_token\n"
                "   get_aws_session_info(environment_token) → credentials_token\n"
                "\n"
                "2. CREATE RESOURCES:\n"
                "   generate_infrastructure_code(resource_type, credentials_token, properties, region) → generated_code_token\n"
                "   explain(generated_code_token, operation='create') → explained_token (STOP: show explanation)\n"
                "   run_checkov(explained_token) → security_scan_token (STOP: show security results)\n"
                "   create_resource(resource_type, credentials_token, explained_token, security_scan_token, region)\n"
                "\n"
                "3. LIST/GET RESOURCES:\n"
                "   list_resources(resource_type, region) → resource list\n"
                "   get_resource(resource_type, identifier, region) → resource details\n"
                "\n"
                "4. UPDATE RESOURCES:\n"
                "   generate_infrastructure_code(resource_type, credentials_token, identifier, patch_document, region) → generated_code_token\n"
                "   explain(generated_code_token, operation='update') → explained_token\n"
                "   run_checkov(explained_token) → security_scan_token\n"
                "   update_resource(resource_type, identifier, credentials_token, explained_token, security_scan_token, patch_document, region)\n"
                "\n"
                "5. DELETE RESOURCES:\n"
                "   get_resource(resource_type, identifier, region) → resource properties\n"
                "   explain(content=resource_properties, operation='delete') → explained_token (STOP: show deletion plan)\n"
                "   delete_resource(resource_type, identifier, credentials_token, explained_token, region, confirmed=true)\n"
                "\n"
                "DELETION WORKFLOW DETAILS:\n"
                "- After explain() for deletion, ALWAYS show the explanation and ask: 'Proceed with deletion? (yes/no)'\n"
                "- If user confirms, call delete_resource() with the explained_token\n"
                "- If user declines, stop and explain cancellation\n"
                "- Example response: 'I have the deletion plan ready. This will permanently terminate instance i-12345. Proceed? (yes/no)'\n"
                "\n"
                "CRITICAL PARAMETER RULES:\n"
                "- CREATE: Use 'properties' parameter (e.g., properties={'InstanceType': 't2.micro'})\n"
                "- UPDATE: Use 'patch_document' parameter with RFC 6902 JSON Patch format\n"
                "- Always include: resource_type='AWS::<Service>::<ResourceType>', region, credentials_token\n"
                "- Common types: AWS::EC2::Instance, AWS::S3::Bucket, AWS::RDS::DBInstance, AWS::Lambda::Function\n"
                "\n"
                "STOP after each explain() call - show results and ask for user confirmation before proceeding.\n"
                "For DELETE operations: After explain(), always ask 'Proceed with deletion? (yes/no)' and wait for confirmation.\n"
                "If confirmed, immediately call delete_resource() with the explained_token.\n"
            )
        
    async def run(self, user_input: str, credentials: dict = None, keycloak_id: str = None):
        # Use keycloak_id as session_id for user isolation
        session_id = keycloak_id or 'default-session'
        
        user_prompt = f"{user_input}\nReturn JSON format responses without markdown formatting. Return MCP server results unmodified unless requested."

        # Load user's persisted tokens and conversation history
        session_tokens = load_user_tokens(session_id)
        conversation_history = session_tokens.get('conversation_history', [])
        
        # Add conversation history context if available
        if conversation_history:
            history_context = "\n=== RECENT CONVERSATION HISTORY ===\n"
            # Show last 3 exchanges for context
            recent_history = conversation_history[-6:]  # Last 3 user+assistant pairs
            for i in range(0, len(recent_history), 2):
                if i + 1 < len(recent_history):
                    user_msg = recent_history[i]
                    assistant_msg = recent_history[i + 1]
                    history_context += f"User: {user_msg}\n"
                    history_context += f"Assistant: {assistant_msg}\n\n"
            history_context += "=== END HISTORY ===\n\n"
            user_prompt = history_context + user_prompt

        if self.CLOUD_TYPE == "AWS":
            existing_creds = session_tokens.get('credentials_token')
            existing_env = session_tokens.get('environment_token')
            existing_code = session_tokens.get('generated_code_token')
            existing_explained = session_tokens.get('explained_token')
            existing_explained_del = session_tokens.get('explained_deletion_token')
            existing_sec = session_tokens.get('security_scan_token')
            existing_req = session_tokens.get('request_token')

            hints: list[str] = []

            if existing_creds:
                hints.append(f"SESSION: credentials_token={existing_creds} (reuse; skip env/session setup)")
                hints.append("CRITICAL: If this credential token fails with 'invalid' or 'expired' error, immediately clear session and get fresh credentials!")
                print(f"Reusing existing credentials_token: {existing_creds}")
            elif existing_env:
                hints.append(f"SESSION: environment_token={existing_env}; call get_aws_session_info(environment_token='{existing_env}')")
                print(f"Reusing existing environment_token: {existing_env}")
            if existing_code:
                hints.append(f"SESSION: generated_code_token={existing_code} (use for explain/run_checkov/create)")
                print(f"Reusing existing generated_code_token: {existing_code}")
            if existing_explained:
                hints.append(f"SESSION: explained_token={existing_explained} (use for run_checkov/create/update/delete)")
                print(f"Reusing existing explained_token: {existing_explained}")
            if existing_explained_del:
                hints.append(f"SESSION: explained_deletion_token={existing_explained_del} (use for delete)")
                print(f"Reusing existing explained_deletion_token: {existing_explained_del}")
            if existing_sec:
                hints.append(f"SESSION: security_scan_token={existing_sec} (include in create/update if enabled)")
                print(f"Reusing existing security_scan_token: {existing_sec}")
            if credentials and not existing_creds:
                # Add credentials
                ak = credentials.get("AWS_ACCESS_KEY")
                hints.append(f"AWS_ACCESS_KEY: {ak}\n")
                sk = credentials.get("AWS_SECRET_ACCESS_KEY")
                hints.append(f"AWS_SECRET_ACCESS_KEY: {sk}\n")
                hints.append("CREDENTIALS PROVIDED: start with check_environment_variables() → get_aws_session_info()")

            if hints:
                user_prompt = "\n".join(hints) + "\n\n" + user_prompt

        if credentials and self.CLOUD_TYPE == "Proxmox":
            creds = []
            if credentials.get('host'): creds.append(f"proxmox_host: {credentials['host']}")
            if credentials.get('username'): creds.append(f"proxmox_username: {credentials['username']}")
            if credentials.get('password'): creds.append(f"proxmox_password: {credentials['password']}")
            if creds:
                user_prompt = f"PROXMOX CREDENTIALS: {', '.join(creds)}\n" + user_prompt

        start_time = time.time()

        agent = Agent(
            name="Assistant",
            system_prompt=self.SYSTEM_PROMPT,
            model=self.model,
            #tools=[duckduckgo_search_tool()],
            toolsets=[self.server],
            prepare_tools=self.TOOL_FILTER
        )

        async with agent.run_mcp_servers():
            try:
                result = await agent.run(user_prompt)
                
                # Extract and save new tokens
                new_tokens = extract_tokens(result)
                if new_tokens:
                    all_tokens = {**session_tokens, **new_tokens}
                else:
                    all_tokens = session_tokens
                
                # Update conversation history
                conversation_history = all_tokens.get('conversation_history', [])
                conversation_history.append(user_input)  # Add user input
                conversation_history.append(str(result.output))  # Add assistant response
                
                # Keep only last 20 messages (10 exchanges) to prevent bloat
                if len(conversation_history) > 20:
                    conversation_history = conversation_history[-20:]
                
                all_tokens['conversation_history'] = conversation_history
                save_user_tokens(session_id, all_tokens)

            except Exception as e:
                return {"error": str(e)}

            return result
    
@staticmethod
async def filter_aws_tools(
    ctx: RunContext[None], tool_defs: list[ToolDefinition]
) -> Union[list[ToolDefinition], None]:
    """Filter to only AWS tools + DuckDuckGo search"""
    aws_tools = {
        # Core CCAPI MCP tools
        "check_environment_variables",
        "get_aws_session_info",
        "get_aws_account_info",
        "get_resource_schema_information",
        "list_resources",
        "get_resource",
        "get_resource_request_status",
        "generate_infrastructure_code",
        "explain",
        "run_checkov",
        "create_resource",
        "update_resource",
        "delete_resource",
        "create_template",
        # Utility
        "duckduckgo_search",
    }
    return [tool_def for tool_def in tool_defs if tool_def.name in aws_tools]

@staticmethod
async def filter_azure_tools(
    ctx: RunContext[None], tool_defs: list[ToolDefinition]
) -> Union[list[ToolDefinition], None]:
    """Filter to only Azure tools"""
    azure_tools = [
        "hello_azure_tools"
    ]
    return [tool_def for tool_def in tool_defs if tool_def.name in azure_tools]

@staticmethod
async def filter_gcp_tools(
    ctx: RunContext[None], tool_defs: list[ToolDefinition]
) -> Union[list[ToolDefinition], None]:
    """Filter to only GCP tools"""
    gcp_tools = [
        "hello_gcp", "list_gcp_vms"
    ]
    return [tool_def for tool_def in tool_defs if tool_def.name in gcp_tools]
    
@staticmethod
async def filter_proxmox_tools(
    ctx: RunContext[None], tool_defs: list[ToolDefinition]
) -> Union[list[ToolDefinition], None]:
    """Filter to only Proxmox tools"""
    proxmox_tools = [
        "list_vms"
    ]
    return [tool_def for tool_def in tool_defs if tool_def.name in proxmox_tools]

# Provider-specific agent classes

class AWSAgent(CloudAgentBase):
    CLOUD_TYPE = "AWS"
    TOOL_FILTER = filter_aws_tools

class AzureAgent(CloudAgentBase):
    CLOUD_TYPE = "Azure"
    TOOL_FILTER = filter_azure_tools

class GCPAgent(CloudAgentBase):
    CLOUD_TYPE = "GCP"
    TOOL_FILTER = filter_gcp_tools

class ProxmoxAgent(CloudAgentBase):
    CLOUD_TYPE = "Proxmox"
    TOOL_FILTER = filter_proxmox_tools

# Factory functions for compatibility with keycloak_id support
async def run_aws_agent(user_input, credentials: dict = None, keycloak_id: str = None):
    return await AWSAgent().run(user_input, credentials, keycloak_id=keycloak_id)

async def run_azure_agent(user_input, credentials: dict = None, keycloak_id: str = None):
    return await AzureAgent().run(user_input, credentials, keycloak_id=keycloak_id)

async def run_gcp_agent(user_input, credentials: dict = None, keycloak_id: str = None):
    return await GCPAgent().run(user_input, credentials, keycloak_id=keycloak_id)

async def run_proxmox_agent(user_input, credentials: dict = None, keycloak_id: str = None):
    return await ProxmoxAgent().run(user_input, credentials, keycloak_id=keycloak_id)