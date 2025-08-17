import os, time
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE
from pydantic_ai.tools import ToolDefinition
from pydantic_ai.result import RunContext
from dotenv import load_dotenv
from typing import Union, Callable
import logfire
from rich.console import Console

console = Console()

load_dotenv()

MODEL = os.getenv("MODEL")
MCP_SERVER_URL = "http://localhost:8000/sse"

logfire.configure(token=os.getenv("LOGFIRE_TOKEN"))
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
            f"Use the right MCP tools to answer user queries as accurately as possible.\n"
            f"Infer the right arguments for the tools based on the user input.\n"
        )

    async def run(self, user_input: str):
        user_prompt = (
            f"{user_input}\n"
            "Always try to return a valid JSON format response without using '''json '''.\n"
            "Always return the result exactly the same from the MCP server, don't modify it unless explicitly asked.\n"
        )

        # Debug info
        console.print(f"System prompt length: {len(self.SYSTEM_PROMPT)} chars")
        console.print(f"User prompt length: {len(user_prompt)} chars")
        console.print(f"Total input length: {len(self.SYSTEM_PROMPT + user_prompt)} chars")

        start_time = time.time()

        agent = Agent(
            name="Assistant",
            system_prompt=self.SYSTEM_PROMPT,
            model=self.model,
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
    """Filter to only AWS tools"""
    aws_tools = [
        "create_ec2_instance", "start_ec2_instance", "stop_ec2_instance", 
        "terminate_ec2_instance", "list_ec2_instances", "get_ami_by_os", 
        "get_default_ami", "create_s3_bucket", "delete_s3_bucket", "delete_s3_bucket_object",
        "list_s3_buckets", "list_s3_bucket_objects"
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

    async def run(self, user_input: str):
        # Get available tools for this agent
        tool_defs = await self.TOOL_FILTER(None, self.server.tools)
        print("[ProxmoxAgent] tool_defs:", tool_defs)
        if not tool_defs:
            print("[ProxmoxAgent] No Proxmox tools available, returning error.")
            return type('Result', (), {'output': "No Proxmox tools are available. Please check your MCP server configuration."})()
        print("[ProxmoxAgent] Proxmox tools found, running agent.")
        return await super().run(user_input)

# Factory functions for compatibility
async def run_aws_agent(user_input):
    return await AWSAgent().run(user_input)

async def run_azure_agent(user_input):
    return await AzureAgent().run(user_input)

async def run_gcp_agent(user_input):
    return await GCPAgent().run(user_input)

async def run_proxmox_agent(user_input):
    return await ProxmoxAgent().run(user_input)