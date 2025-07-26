import os, time
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE
from pydantic_ai.tools import ToolDefinition
from pydantic_ai.result import RunContext
from dotenv import load_dotenv
from typing import Union
import logfire
from rich.console import Console

console = Console()

load_dotenv()

MODEL = os.getenv("MODEL")
MCP_SERVER_URL = "http://localhost:8000/sse"

logfire.configure(token=os.getenv("LOGFIRE_TOKEN"))
logfire.instrument_pydantic_ai()

server = MCPServerSSE(url=MCP_SERVER_URL)

async def filter_aws_tools(
    ctx: RunContext[None], tool_defs: list[ToolDefinition]
) -> Union[list[ToolDefinition], None]:
    """Filter to only AWS tools"""
    aws_tools = [
        "create_ec2_instance", "start_ec2_instance", "stop_ec2_instance", 
        "terminate_ec2_instance", "list_ec2_instances", "get_ami_by_os", 
        "get_default_ami", "create_s3_bucket", "delete_s3_bucket", 
        "list_s3_buckets", "list_s3_bucket_objects"
    ]
    return [tool_def for tool_def in tool_defs if tool_def.name in aws_tools]

async def filter_azure_tools(
    ctx: RunContext[None], tool_defs: list[ToolDefinition]
) -> Union[list[ToolDefinition], None]:
    """Filter to only Azure tools"""
    azure_tools = [
        "hello_azure_tools"
    ]
    return [tool_def for tool_def in tool_defs if tool_def.name in azure_tools]

async def filter_gcp_tools(
    ctx: RunContext[None], tool_defs: list[ToolDefinition]
) -> Union[list[ToolDefinition], None]:
    """Filter to only GCP tools"""
    gcp_tools = [
        "hello_gcp", "list_gcp_vms"
    ]
    return [tool_def for tool_def in tool_defs if tool_def.name in gcp_tools]

# AWS agent
async def run_aws_agent(user_input):
    """Shared AWS agent function"""
    SYSTEM_PROMPT = (
        "You are a helpful assistant for AWS management.\n"
        "Use the right MCP tools to answer user queries as accurately as possible.\n"
    )

    user_prompt = f"{user_input}\n \
    Always try to return a valid JSON format response without using '''json '''.\n \
    Always return the result exactly the same from the MCP server, don't modify it unless explicitly asked.\n"
    
    # Used for debugging
    console.print(f"System prompt length: {len(SYSTEM_PROMPT)} chars")
    console.print(f"User prompt length: {len(user_prompt)} chars")
    console.print(f"Total input length: {len(SYSTEM_PROMPT + user_prompt)} chars")

    start_time = time.time()

    agent = Agent(
        name="Assistant",
        system_prompt=SYSTEM_PROMPT,
        model=MODEL,
        mcp_servers=[server],
        prepare_tools=filter_aws_tools
    )
    
    async with agent.run_mcp_servers():
        console.print("Running agent...")

        result = await agent.run(user_prompt)

        end_time = time.time()
        duration = end_time - start_time

        console.print(f"\n[bold green]✅ AGENT COMPLETED[/bold green]")
        console.print(f"Duration: {duration:.2f} seconds")

        return result

# Azure agent
async def run_azure_agent(user_input):
    """Shared Azure agent function"""
    SYSTEM_PROMPT = (
        "You are a helpful assistant for Azure management.\n"
        "Use the right MCP tools to answer user queries as accurately as possible.\n"
    )

    user_prompt = f"{user_input}\n \
    Always try to return a valid JSON format response without using '''json '''.\n \
    Always return the result exactly the same from the MCP server, don't modify it unless explicitly asked.\n"
    
    # Used for debugging
    console.print(f"System prompt length: {len(SYSTEM_PROMPT)} chars")
    console.print(f"User prompt length: {len(user_prompt)} chars")
    console.print(f"Total input length: {len(SYSTEM_PROMPT + user_prompt)} chars")

    start_time = time.time()

    agent = Agent(
        name="Assistant",
        system_prompt=SYSTEM_PROMPT,
        model=MODEL,
        mcp_servers=[server],
        prepare_tools=filter_azure_tools

    )
    
    async with agent.run_mcp_servers():
        console.print("Running agent...")

        result = await agent.run(user_prompt)

        end_time = time.time()
        duration = end_time - start_time

        console.print(f"\n[bold green]✅ AGENT COMPLETED[/bold green]")
        console.print(f"Duration: {duration:.2f} seconds")

        return result

# GCP agent
async def run_gcp_agent(user_input):
    """Shared GCP agent function"""
    SYSTEM_PROMPT = (
        "You are a helpful assistant for GCP management.\n"
        "Use the right MCP tools to answer user queries as accurately as possible.\n"
    )

    user_prompt = f"{user_input}\n \
    Always try to return a valid JSON format response without using '''json '''.\n \
    Always return the result exactly the same from the MCP server, don't modify it unless explicitly asked.\n"
    
    # Used for debugging
    console.print(f"System prompt length: {len(SYSTEM_PROMPT)} chars")
    console.print(f"User prompt length: {len(user_prompt)} chars")
    console.print(f"Total input length: {len(SYSTEM_PROMPT + user_prompt)} chars")

    start_time = time.time()

    agent = Agent(
        name="Assistant",
        system_prompt=SYSTEM_PROMPT,
        model=MODEL,
        mcp_servers=[server],
        prepare_tools=filter_gcp_tools

    )
    
    async with agent.run_mcp_servers():
        console.print("Running agent...")

        result = await agent.run(user_prompt)

        end_time = time.time()
        duration = end_time - start_time

        console.print(f"\n[bold green]✅ AGENT COMPLETED[/bold green]")
        console.print(f"Duration: {duration:.2f} seconds")

        return result