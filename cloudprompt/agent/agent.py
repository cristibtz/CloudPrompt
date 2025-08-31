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
MCP_SERVER_URL = "http://127.0.0.1:8088/sse"

logfire.configure(token=os.getenv("LOGFIRE_TOKEN"), scrubbing=False)
logfire.instrument_pydantic_ai()

server = MCPServerSSE(url=MCP_SERVER_URL)

SESSION_STORE = InMemorySessionStore()

def _load_tokens(session_id: Optional[str]) -> dict[str, str]:
    return SESSION_STORE.load(session_id)

def _save_tokens(session_id: Optional[str], tokens: dict[str, str]) -> None:
    SESSION_STORE.save(session_id, tokens)

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
                    'security_scan_token',
                    'request_token',
                } and isinstance(v, str):
                    found[k] = v
        elif isinstance(obj, list):
            for item in obj:
                _scan_obj(item)

    def _scan_text(text: str):
        patterns = {
            'environment_token': r'(env_[a-f0-9\-]{16,})',
            'credentials_token': r'(creds_[a-f0-9\-]{16,})',
            'generated_code_token': r'(generated_code_[a-f0-9\-]{16,})',
            'explained_token': r'(explained_[a-f0-9\-]{16,})',
            'security_scan_token': r'(sec_[a-f0-9\-]{16,})',
        }
        for name, pat in patterns.items():
            m = re.search(pat, text)
            if m and name not in found:
                found[name] = m.group(1)

    _scan_obj(result)
    if isinstance(result, str):
        _scan_text(result)
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
                f"3) Pass credentials_token to ALL subsequent AWS tools: list_resources, get_resource, get_resource_request_status, generate_infrastructure_code, create_resource, update_resource, delete_resource.\n"
                f"CREATE/UPDATE SEQUENCE:\n"
                f"- Never call generate_infrastructure_code with empty properties. Provide minimally-required properties first.\n"
                f"- If a required property is unknown, ask ONE concise question or do a brief search, then proceed.\n"
                f"- Example minimums: EC2 Instance → ImageId, InstanceType (+SubnetId/SecurityGroupIds if needed); S3 Bucket → BucketName (optional), Tags.\n"
                f"- After generate_infrastructure_code → explain (show explanation), then run_checkov, then create/update with explained_token (+security_scan_token when available).\n"
                f"DELETE SEQUENCE: get_resource → explain(operation=delete) → delete_resource(confirmed=True).\n"
                f"Always include credentials_token and region when calling list/get/status and resource ops.\n"
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

        # If security scanning is disabled on server, guide tools to pass skip_security_check=True
        if os.getenv('SECURITY_SCANNING', '').lower() == 'disabled':
            user_prompt = (
                "SECURITY_SCANNING is disabled on the server. When calling create_resource() or update_resource(), set skip_security_check=True.\n"
                + user_prompt
            )

        # Add credentials instruction if provided
        # Load any persisted tokens for this session and inject them
        session_tokens = _load_tokens(session_id)

        if (credentials or session_tokens) and self.CLOUD_TYPE == "AWS":
                cred_instruction = "\nIMPORTANT: Use explicit AWS credentials with the MCP tools.\nFollow: check_environment_variables → get_aws_session_info → thread credentials_token into list/get/status and all resource operations.\nParameters for check_environment_variables():\n"
                # Support multiple key shapes
                access_key = None
                secret_key = None
                session_token = None
                region = None
                if credentials:
                    access_key = credentials.get('access_key') or credentials.get('AWS_ACCESS_KEY') or credentials.get('AWS_ACCESS_KEY_ID')
                    secret_key = credentials.get('secret_key') or credentials.get('AWS_SECRET_KEY') or credentials.get('AWS_SECRET_ACCESS_KEY')
                    session_token = credentials.get('session_token') or credentials.get('AWS_SESSION_TOKEN')
                    region = credentials.get('region') or credentials.get('AWS_REGION')
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
                # If caller already has workflow tokens from a previous turn, reuse them directly
                existing_creds_token = (credentials or {}).get('credentials_token') or session_tokens.get('credentials_token')
                existing_env_token = (credentials or {}).get('environment_token') or session_tokens.get('environment_token')
                existing_gen_token = (credentials or {}).get('generated_code_token') or session_tokens.get('generated_code_token')
                existing_explained = ((credentials or {}).get('explained_token') or (credentials or {}).get('execution_token') or session_tokens.get('explained_token'))
                existing_sec_token = (credentials or {}).get('security_scan_token') or session_tokens.get('security_scan_token')
                existing_request_token = (credentials or {}).get('request_token') or session_tokens.get('request_token')

                if existing_creds_token or existing_env_token or existing_gen_token or existing_explained or existing_sec_token or existing_request_token:
                    cred_instruction += (
                        "\nIf any of these tokens are provided, USE THEM DIRECTLY instead of re-running earlier steps:\n"
                        "- credentials_token: use as-is for list/get/status/create/update/delete\n"
                        "- environment_token: pass to get_aws_session_info to obtain credentials_token\n"
                        "- generated_code_token / explained_token / security_scan_token / request_token: thread them into the appropriate follow-up tool calls\n"
                    )
                    if existing_env_token:
                        cred_instruction += f"- environment_token: {existing_env_token}\n"
                    if existing_creds_token:
                        cred_instruction += f"- credentials_token: {existing_creds_token}\n"
                    if existing_gen_token:
                        cred_instruction += f"- generated_code_token: {existing_gen_token}\n"
                    if existing_explained:
                        cred_instruction += f"- explained_token: {existing_explained}\n"
                    if existing_sec_token:
                        cred_instruction += f"- security_scan_token: {existing_sec_token}\n"
                    if existing_request_token:
                        cred_instruction += f"- request_token: {existing_request_token}\n"

                cred_instruction += (
                    "Rules:\n"
                    "- Do NOT call generate_infrastructure_code without a non-empty properties object.\n"
                    "- If creating an EC2 instance and AMI is unknown, either ask the user for ImageId or quickly look up a suitable AMI, then proceed.\n"
                )
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
        console.print(f"System prompt length: {len(self.SYSTEM_PROMPT)} chars")
        console.print(f"User prompt length: {len(user_prompt)} chars")
        console.print(f"Total input length: {len(self.SYSTEM_PROMPT + user_prompt)} chars")

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
                # Persist any discovered tokens for this session
                tokens = _extract_tokens_from_result(result)
                _save_tokens(session_id, tokens)
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