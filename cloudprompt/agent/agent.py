import os, time
from pydantic_ai import Agent, WebSearchTool
from pydantic_ai.mcp import MCPServerStreamableHTTP
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
MCP_SERVER_URL = "http://localhost:8000/mcp"

logfire.configure(token=os.getenv("LOGFIRE_TOKEN"), scrubbing=False)
logfire.instrument_pydantic_ai()

server = MCPServerStreamableHTTP(url=MCP_SERVER_URL)


class CloudAgentBase:
    CLOUD_TYPE = "Cloud"
    TOOL_FILTER: Callable = None

    def __init__(self):
        self.model = MODEL
        self.server = server
        self.SYSTEM_PROMPT = (
            f"You are a helpful assistant for {self.CLOUD_TYPE} management.\n"
            f"Use the right MCP tools to answer user queries as accurately as possible.\n"
            f"If an MCP tool is not proper, search the web for the information.\n"
            f"Don't hesitate to execute a tool if this is what the user asked. Don't ask for confirmations regarding creating, \
            deleteting, updating, or listing resources.\n\n"

            f"IMPORTANT:\n"
            f"After you completed the tasks, list all the tools you(and how many times you tried to use them) used in the format: 'Tools used: tool1, tool2, tool3'"
        )

    async def run(self, user_input: str, credentials: dict = None):
        user_prompt = (
            f"{user_input}\n"
            "Always try to return a valid JSON format response without using '''json '''.\n"
            "Always return the result exactly the same from the MCP server, don't modify it unless explicitly asked.\n"
            "If you need to figure out some information, use the builtin web search tool to find the information.\n"
        )

        if self.CLOUD_TYPE == "AWS":
            self.SYSTEM_PROMPT += (
                f"IMPORTANT FOR AWS OPERATIONS:\n"
                f"1. ALWAYS call 'authenticate_aws' FIRST before any other AWS tools\n"
                f"2. Use the session_id returned from authentication for all subsequent AWS operations\n"
                f"3. If authentication fails, inform the user and do not proceed with other AWS operations\n"
                f"4. All AWS tools require an authenticated session to work properly\n"
            )

        if self.CLOUD_TYPE == "Proxmox":
            self.SYSTEM_PROMPT += (
                f"IMPORTANT FOR PROXMOX OPERATIONS:\n"
                f"1. ALWAYS call 'authenticate_proxmox' FIRST before any other Proxmox tools\n"
                f"2. Use the session_id returned from authentication for all subsequent Proxmox operations\n"
                f"3. If authentication fails, inform the user and do not proceed with other Proxmox operations\n"
                f"4. All Proxmox tools require an authenticated session to work properly\n"
            )

        # Add credentials instruction if provided
        if credentials and self.CLOUD_TYPE == "AWS":
            cred_instruction = "\nIMPORTANT: Use these credentials when calling authenticate_aws:\n"
            if "AWS_ACCESS_KEY" in credentials:
                cred_instruction += f"- aws_access_key_id: {credentials['AWS_ACCESS_KEY']}\n"
            if "AWS_SECRET_ACCESS_KEY" in credentials:
                cred_instruction += f"- aws_secret_access_key: {credentials['AWS_SECRET_ACCESS_KEY']}\n"
            cred_instruction += "Call authenticate_aws with these credentials BEFORE any other AWS operations.\n"
            user_prompt = cred_instruction + user_prompt
        
        if credentials and self.CLOUD_TYPE == "Proxmox":
            cred_instruction = "\nIMPORTANT: Use these credentials when calling authenticate_proxmox:\n"
            if "host" in credentials:
                cred_instruction += f"- host: {credentials['host']}\n"
            if "username" in credentials:
                cred_instruction += f"- username: {credentials['username']}\n"
            if "token_name" in credentials:
                cred_instruction += f"- token_name: {credentials['token_name']}\n"
            if "token_value" in credentials:
                cred_instruction += f"- token_value: {credentials['token_value']}\n"
            cred_instruction += "Call authenticate_proxmox with these credentials BEFORE any other Proxmox operations.\n"
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
    aws_tools = [
        "authenticate_aws", "get_amis", "create_ec2_instance", "start_ec2_instance", 
        "stop_ec2_instance", "terminate_ec2_instance", "list_ec2_instances", 
        "list_ec2_instance", "create_s3_bucket", "delete_s3_bucket", 
        "delete_s3_bucket_object", "list_s3_buckets", "list_s3_bucket_objects", 
        "create_ssh_key_pair", "list_ssh_key_pairs", "delete_ssh_key_pair", 
        "duckduckgo_search"
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
        "authenticate_proxmox", "list_vms", "list_proxmox_nodes", "create_vm", "delete_vm", 
        "start_vm", "stop_vm", "list_iso_images", "duckduckgo_search"
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