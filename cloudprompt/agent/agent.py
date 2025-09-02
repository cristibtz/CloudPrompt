import os, time
from pydantic_ai import Agent, WebSearchTool
from pydantic_ai.mcp import MCPServerSSE
from pydantic_ai.tools import ToolDefinition
from pydantic_ai.result import RunContext
from dotenv import load_dotenv
from typing import Union, Callable, Optional, Any
import re
import logfire
from rich.console import Console
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai.toolsets import CombinedToolset
from .session_store import InMemorySessionStore


console = Console()

load_dotenv()

MODEL = os.getenv("MODEL")
MCP_SERVER_URL = "http://127.0.0.1:8089/sse"

logfire.configure(token=os.getenv("LOGFIRE_TOKEN"), scrubbing=False)
logfire.instrument_pydantic_ai()

server = MCPServerSSE(url=MCP_SERVER_URL)

SESSION_STORE = InMemorySessionStore()

def _load_tokens(session_id: Optional[str]) -> dict[str, str]:
    return SESSION_STORE.load(session_id)

def _save_tokens(session_id: Optional[str], tokens: dict[str, str]) -> None:
    SESSION_STORE.save(session_id, tokens)

def clear_session(session_id: Optional[str]) -> None:
    """Clear session tokens for debugging or logout"""
    SESSION_STORE.clear_session(session_id)

def clear_invalid_tokens(session_id: Optional[str]) -> None:
    """Clear potentially invalid tokens when MCP server has restarted"""
    if session_id:
        current_tokens = _load_tokens(session_id)
        # Keep only environment tokens as they can be reused, clear workflow tokens
        valid_tokens = {k: v for k, v in current_tokens.items() if k in ['environment_token']}
        SESSION_STORE._store[session_id] = valid_tokens
        SESSION_STORE._save_to_disk(session_id)
        console.print(f"[yellow]🔄 Cleared invalid workflow tokens for session '{session_id}'[/yellow]")

def list_sessions() -> dict:
    """List all active sessions for debugging"""
    return SESSION_STORE.list_sessions()

def test_session_management(session_id: str = "test-session") -> None:
    """Test function to verify session management is working"""
    console.print(f"[cyan]🧪 Testing session management with session_id: {session_id}[/cyan]")
    
    # Test saving tokens
    test_tokens = {
        'environment_token': 'env_12345678-1234-1234-1234-123456789abc',
        'credentials_token': 'creds_87654321-4321-4321-4321-cba987654321'
    }
    
    console.print(f"[cyan]💾 Saving test tokens: {list(test_tokens.keys())}[/cyan]")
    _save_tokens(session_id, test_tokens)
    
    # Test loading tokens
    console.print(f"[cyan]📥 Loading tokens...[/cyan]")
    loaded_tokens = _load_tokens(session_id)
    console.print(f"[cyan]📋 Loaded tokens: {list(loaded_tokens.keys())}[/cyan]")
    
    # Verify they match
    if loaded_tokens == test_tokens:
        console.print(f"[green]✅ Session management test PASSED[/green]")
    else:
        console.print(f"[red]❌ Session management test FAILED[/red]")
        console.print(f"[red]Expected: {test_tokens}[/red]")
        console.print(f"[red]Got: {loaded_tokens}[/red]")
    
    # Clean up
    clear_session(session_id)

def _extract_tokens_from_result(result: Any) -> dict[str, str]:
    """Best-effort extraction of MCP workflow tokens from result payloads."""
    found: dict[str, str] = {}

    def _scan_obj(obj: Any):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    _scan_obj(v)
                elif isinstance(v, str):
                    _scan_text(v)
                # Direct named keys
                if k in {
                    'environment_token',
                    'credentials_token',
                    'generated_code_token',
                    'explained_token',
                    'execution_token',  # Sometimes used instead of explained_token
                    'security_scan_token',
                    'request_token',
                } and isinstance(v, str) and v not in found.values():
                    # Map execution_token to explained_token for consistency
                    token_key = 'explained_token' if k == 'execution_token' else k
                    found[token_key] = v
                    console.print(f"[dim]🔑 Found {token_key} via key: {v}[/dim]")
        elif isinstance(obj, list):
            for item in obj:
                _scan_obj(item)

    def _scan_text(text: str):
        patterns = {
            'environment_token': r'\b(env_[a-f0-9\-]{8,})\b',
            'credentials_token': r'\b(creds_[a-f0-9\-]{8,})\b',
            'generated_code_token': r'\b(generated_code_[a-f0-9\-]{8,})\b',
            'explained_token': r'\b(explained_[a-f0-9\-]{8,})\b',
            'execution_token': r'\b(execution_[a-f0-9\-]{8,})\b',
            'security_scan_token': r'\b(sec_[a-f0-9\-]{8,})\b',
            'request_token': r'\b(req_[a-f0-9\-]{8,})\b',
        }
        for name, pat in patterns.items():
            matches = re.findall(pat, text)
            if matches and name not in found:
                # Take the first match found and map execution_token to explained_token
                token_key = 'explained_token' if name == 'execution_token' else name
                found[token_key] = matches[0]
                # Debug: print found tokens
                console.print(f"[dim]🔍 Found {token_key}: {matches[0]}[/dim]")

    _scan_obj(result)
    if isinstance(result, str):
        _scan_text(result)
    
    # Also check the result object's attributes if it has them
    if hasattr(result, 'data') and result.data:
        _scan_obj(result.data)
    if hasattr(result, 'output') and result.output:
        # Handle the case where result.output is a JSON string
        if isinstance(result.output, str):
            try:
                import json
                parsed_output = json.loads(result.output)
                _scan_obj(parsed_output)
            except json.JSONDecodeError:
                # If it's not valid JSON, treat as text
                _scan_text(result.output)
        else:
            _scan_obj(result.output)
    
    return found


class CloudAgentBase:
    CLOUD_TYPE = "Cloud"
    TOOL_FILTER: Callable = None

    def __init__(self):
        self.model = MODEL
        self.server = server
        self.SYSTEM_PROMPT = (
            f"You are a helpful assistant for {self.CLOUD_TYPE} management.\n"
            f"Use the provided MCP tools first; use web search only when a small missing fact blocks progress.\n"
        )

        if self.CLOUD_TYPE == "AWS":
            self.SYSTEM_PROMPT += (
                f"CRITICAL AWS FLOW (always in this order for any AWS operation):\n"
                f"1) check_environment_variables(aws_access_key_id, aws_secret_access_key, aws_session_token?, region?)\n"
                f"2) get_aws_session_info(environment_token) → credentials_token\n"
                f"3) generate_infrastructure_code(resource_type, properties, credentials_token) → generated_code_token\n"
                f"4) explain(generated_code_token) → explained_token\n"
                f"5) run_checkov(generated_code_token) → security_scan_token\n"
                f"6) create_resource(resource_type, operation, explained_token, region?, identifier?)\n"
                f"\n"
                f"TOOL USAGE NOTES:\n"
                f"- generate_infrastructure_code: Use 'properties' field for new resources, 'patch_document' only for updates\n"
                f"- For NEW S3 bucket with versioning: properties={{'BucketName': 'bucket-name', 'VersioningConfiguration': {{'Status': 'Enabled'}}}}\n"
                f"- For resource UPDATES: use patch_document with JSON patch operations\n"
                f"- explain and run_checkov both use generated_code_token from step 3\n"
                f"- create_resource uses explained_token from step 4\n"
                f"- Always pass credentials_token to generate_infrastructure_code\n"
                f"- Leave patch_document empty [] for new resource creation\n"
            )

    async def run(self, user_input: str, credentials: dict = None, session_id: Optional[str] = None):
        # Generate a default session_id if not provided to enable memory by default
        if not session_id:
            session_id = os.getenv('DEFAULT_SESSION_ID') or 'default-session'
        
        user_prompt = (
            f"{user_input}\n"
            "Always try to return a valid JSON format response without using '''json '''.\n"
            "Always return the result exactly the same from the MCP server, don't modify it unless explicitly asked.\n"
            "If you need to figure out some information, use the builtin web search tool to find the information.\n"
        )

        # Load any persisted tokens for this session FIRST
        session_tokens = _load_tokens(session_id)

        if self.CLOUD_TYPE == "AWS":
            # Check if we have existing valid credentials_token from session
            existing_creds_token = session_tokens.get('credentials_token')
            existing_env_token = session_tokens.get('environment_token')
            
            # Prepare credential instruction
            cred_instruction = "\nIMPORTANT AWS WORKFLOW OPTIMIZATION:\n"
            
            if existing_creds_token:
                # We have a valid credentials token - skip authentication steps
                cred_instruction += (
                    f"✅ EXISTING SESSION FOUND: You have a credentials_token from a previous session.\n"
                    f"- credentials_token: {existing_creds_token}\n"
                    f"🚀 TRY REUSING: First try to use this credentials_token directly with AWS resource operations.\n"
                    f"📋 DIRECT USE: Use this credentials_token directly with ANY AWS resource operation:\n"
                    f"   - list_resources(credentials_token='{existing_creds_token}')\n"
                    f"   - get_resource(credentials_token='{existing_creds_token}')\n"
                    f"   - generate_infrastructure_code(credentials_token='{existing_creds_token}')\n"
                    f"⚠️ FALLBACK: If you get 'Invalid token' or 'Workflow store' errors, the MCP server was restarted.\n"
                    f"   In that case, call check_environment_variables() → get_aws_session_info() to get fresh tokens.\n\n"
                )
            elif existing_env_token:
                # We have environment token but need credentials token
                cred_instruction += (
                    f"✅ PARTIAL SESSION FOUND: You have an environment_token from a previous session.\n"
                    f"- environment_token: {existing_env_token}\n"
                    f"⏩ SKIP STEP 1: Do NOT call check_environment_variables().\n"
                    f"▶️ STEP 2 ONLY: Call get_aws_session_info(environment_token='{existing_env_token}') to get credentials_token.\n"
                    f"📋 THEN USE: Use the returned credentials_token for all subsequent AWS operations.\n\n"
                )
            else:
                # No existing tokens - need full authentication flow
                cred_instruction += (
                    f"🔐 NEW SESSION: No existing tokens found. Full authentication required.\n"
                    f"📋 REQUIRED FLOW: check_environment_variables → get_aws_session_info → resource operations\n"
                    f"💡 IMPORTANT: If you get 'Invalid token' or 'Workflow store' errors, the MCP server was restarted.\n"
                    f"   Always start with check_environment_variables() to get fresh tokens.\n"
                )
                
                # Add credential parameters for authentication
                access_key = None
                secret_key = None
                session_token = None
                region = None
                
                if credentials:
                    access_key = credentials.get('access_key') or credentials.get('AWS_ACCESS_KEY') or credentials.get('AWS_ACCESS_KEY_ID')
                    secret_key = credentials.get('secret_key') or credentials.get('AWS_SECRET_KEY') or credentials.get('AWS_SECRET_ACCESS_KEY')
                    session_token = credentials.get('session_token') or credentials.get('AWS_SESSION_TOKEN')
                    region = credentials.get('region') or credentials.get('AWS_REGION')
                
                cred_instruction += f"Parameters for check_environment_variables():\n"
                if access_key:
                    cred_instruction += f"- aws_access_key_id: {access_key}\n"
                if secret_key:
                    cred_instruction += f"- aws_secret_access_key: {secret_key}\n"
                if session_token:
                    cred_instruction += f"- aws_session_token: {session_token}\n"
                if region:
                    cred_instruction += f"- region: {region}\n"
                if not access_key or not secret_key:
                    cred_instruction += (
                        "- If credentials are not present above, ask the user for AWS Access Key ID and Secret Access Key before calling any AWS tool.\n"
                    )
            
            # Add any other existing workflow tokens for context
            other_tokens = []
            for token_type in ['generated_code_token', 'explained_token', 'security_scan_token', 'request_token']:
                token_value = session_tokens.get(token_type)
                if token_value:
                    other_tokens.append(f"- {token_type}: {token_value}")
            
            if other_tokens:
                cred_instruction += f"\n🔗 OTHER SESSION TOKENS (for workflow continuation):\n" + "\n".join(other_tokens) + "\n"
            
            user_prompt = cred_instruction + user_prompt

        if credentials and self.CLOUD_TYPE == "Proxmox":
            cred_instruction = "\nIMPORTANT: When calling Proxmox tools, use these credentials:\n"
            if "host" in credentials:
                cred_instruction += f"- proxmox_host: {credentials['host']}\n"
            if "username" in credentials:
                cred_instruction += f"- proxmox_username: {credentials['username']}\n"
            if "password" in credentials:
                cred_instruction += f"- proxmox_password: {credentials['password']}\n"
            cred_instruction += "Pass these as parameters to all tool function calls.\n"
            user_prompt = cred_instruction + user_prompt

        # Debug info
        console.print(f"[dim]System prompt length: {len(self.SYSTEM_PROMPT)} chars[/dim]")
        console.print(f"[dim]User prompt length: {len(user_prompt)} chars[/dim]")
        console.print(f"[dim]Total input length: {len(self.SYSTEM_PROMPT + user_prompt)} chars[/dim]")
        console.print(f"[cyan]🔑 Session ID: {session_id}[/cyan]")
        
        # Show loaded session state
        current_tokens = _load_tokens(session_id)
        if current_tokens:
            console.print(f"[cyan]📋 Current session tokens: {list(current_tokens.keys())}[/cyan]")
        else:
            console.print(f"[yellow]📋 No existing session tokens found[/yellow]")

        start_time = time.time()

        agent = Agent(
            name="Assistant",
            system_prompt=self.SYSTEM_PROMPT,
            model=self.model,
            tools=[duckduckgo_search_tool()],
            toolsets=[self.server],
            prepare_tools=self.TOOL_FILTER
        )

        async with agent.run_mcp_servers():
            console.print("Running agent...")

            try:
                result = await agent.run(user_prompt)
                # Extract and persist any discovered tokens for this session
                new_tokens = _extract_tokens_from_result(result)
                if new_tokens:
                    # Merge with existing session tokens (new tokens take precedence)
                    existing_tokens = _load_tokens(session_id)
                    merged_tokens = {**existing_tokens, **new_tokens}
                    _save_tokens(session_id, merged_tokens)
                    console.print(f"[cyan]💾 Session tokens updated: {list(new_tokens.keys())}[/cyan]")
                    console.print(f"[cyan]📋 Total session tokens: {list(merged_tokens.keys())}[/cyan]")
                else:
                    console.print(f"[yellow]⚠️ No new tokens extracted from this result[/yellow]")
                    # Debug: Print result structure to understand why no tokens were found
                    console.print(f"[dim]Debug - Result type: {type(result)}[/dim]")
                    if hasattr(result, 'data'):
                        console.print(f"[dim]Debug - Result.data: {str(result.data)[:200]}...[/dim]")
                    if hasattr(result, 'output'):
                        console.print(f"[dim]Debug - Result.output type: {type(result.output)}[/dim]")
                        console.print(f"[dim]Debug - Result.output: {str(result.output)[:200]}...[/dim]")
                    console.print(f"[dim]Debug - Result attributes: {[attr for attr in dir(result) if not attr.startswith('_')]}[/dim]")
                
                # Also try to extract tokens from the entire conversation/tool history
                try:
                    if hasattr(agent, '_conversation') and agent._conversation:
                        conversation_tokens = _extract_tokens_from_result(agent._conversation)
                        if conversation_tokens:
                            existing_tokens = _load_tokens(session_id)
                            all_tokens = {**existing_tokens, **conversation_tokens}
                            _save_tokens(session_id, all_tokens)
                            console.print(f"[cyan]🔍 Additional tokens from conversation: {list(conversation_tokens.keys())}[/cyan]")
                except Exception as e:
                    console.print(f"[dim]Debug - Could not extract from conversation: {e}[/dim]")
            except Exception as e:
                console.print(f"Error occurred: {e}")
                return {"error": str(e)}

            end_time = time.time()
            duration = end_time - start_time

            console.print(f"\n[bold green]✅ AGENT COMPLETED[/bold green]")
            console.print(f"Duration: {duration:.2f} seconds")

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

# Factory functions for compatibility
async def run_aws_agent(user_input, credentials: dict = None, session_id: Optional[str] = None):
    return await AWSAgent().run(user_input, credentials, session_id=session_id)

async def run_azure_agent(user_input, credentials: dict = None, session_id: Optional[str] = None):
    return await AzureAgent().run(user_input, credentials, session_id=session_id)

async def run_gcp_agent(user_input, credentials: dict = None, session_id: Optional[str] = None):
    return await GCPAgent().run(user_input, credentials, session_id=session_id)

async def run_proxmox_agent(user_input, credentials: dict = None, session_id: Optional[str] = None):
    return await ProxmoxAgent().run(user_input, credentials, session_id=session_id)