import os, time
from pydantic_ai import Agent, WebSearchTool
from pydantic_ai.mcp import MCPServerSSE
from pydantic_ai.tools import ToolDefinition
from pydantic_ai.result import RunContext
from dotenv import load_dotenv
from typing import Union, Callable
import logfire
from rich.console import Console
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai.toolsets import CombinedToolset


console = Console()

load_dotenv()

MODEL = os.getenv("MODEL")
MCP_SERVER_URL = "http://localhost:8000/sse"

logfire.configure(token=os.getenv("LOGFIRE_TOKEN"), scrubbing=False)
logfire.instrument_pydantic_ai()

server = MCPServerSSE(url=MCP_SERVER_URL)


class CloudAgentBase:
    CLOUD_TYPE = "Cloud"
    TOOL_FILTER: Callable = None

    def __init__(self):
        self.model = MODEL
        self.server = server
        self.SYSTEM_PROMPT = (
            f"You are a helpful assistant for {self.CLOUD_TYPE} management.\n"
        )

    async def run(self, user_input: str, credentials: dict = None):
        
        user_prompt = (
            f"{user_input}\n"
            f"Use these user credentials: {credentials}\n"
        )

        # Add credentials instruction if provided
        if credentials and self.CLOUD_TYPE == "AWS":
            self.SYSTEM_PROMPT += (
            f"\n"
            f"Example workflow for create/update operations:\n"
            f"1. check_environment_variables() → environment_token\n"
            f"2. get_aws_session_info(environment_token) → credentials_token\n"
            f"OPTIONAL: If you need extra info about resource properties, use duckduckgo_search(), but only twice\n"
            f"3. generate_infrastructure_code(credentials_token, resource_type, properties) → generated_code_token\n"
            f"4. explain(generated_code_token) → explained_token\n"
            f"5. run_checkov(explained_token) → security_scan_token (if security enabled)\n"
            f"6. create_resource(credentials_token, explained_token, security_scan_token)\n"
            f"\n"
            f"IMPORTANT:\n"
            f"- Always provide properties for generate_infrastructure_code\n"
            f"Example:"
            f"- Follow the exact token workflow - each step requires the token from the previous step\n"
            f"- Use get_resource_schema_information() if you need property details\n"

            f"No-token tools: get_resource(), list_resources(), get_resource_schema_information(), create_template(), get_aws_account_info()\n"
            f"Security scanning is disabled. Use skip_security_scan=True in create_resource to bypass security checks.\n"
        )
        
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
            except Exception as e:
                error_msg = str(e)
                console.print(f"[red]❌ Error: {error_msg}[/red]")
                
                return {"error": error_msg}

            end_time = time.time()
            duration = end_time - start_time

            console.print(f"\n[bold green]✅ AGENT COMPLETED[/bold green]")
            console.print(f"Duration: {duration:.2f} seconds")

            return result
    

'''@staticmethod
async def filter_aws_tools(
    ctx: RunContext[None], tool_defs: list[ToolDefinition]
) -> Union[list[ToolDefinition], None]:
    """Filter to only AWS tools + DuckDuckGo search"""
    aws_tools = [
        "create_ec2_instance", "start_ec2_instance", "stop_ec2_instance", 
        "terminate_ec2_instance", "list_ec2_instances", "get_amis", 
        "create_s3_bucket", "delete_s3_bucket", "delete_s3_bucket_object",
        "list_s3_buckets", "list_s3_bucket_objects", "duckduckgo_search",
    ]
    return [tool_def for tool_def in tool_defs if tool_def.name in aws_tools]
'''

@staticmethod
async def filter_aws_tools(
    ctx: RunContext[None], tool_defs: list[ToolDefinition]
) -> Union[list[ToolDefinition], None]:
    """Filter to only AWS tools"""
    aws_tools = [
        "check_environment_variables", "get_aws_session_info", "get_aws_account_info",
        "get_resource_schema_information", "list_resources", "get_resource",
        "generate_infrastructure_code", "explain", "run_checkov",
        "create_resource", "update_resource", "delete_resource"
    ]
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
async def run_aws_agent(user_input, credentials: dict = None):
    return await AWSAgent().run(user_input, credentials)

async def run_azure_agent(user_input, credentials: dict = None):
    return await AzureAgent().run(user_input, credentials)

async def run_gcp_agent(user_input, credentials: dict = None):
    return await GCPAgent().run(user_input, credentials)

async def run_proxmox_agent(user_input, credentials: dict = None):
    return await ProxmoxAgent().run(user_input, credentials)