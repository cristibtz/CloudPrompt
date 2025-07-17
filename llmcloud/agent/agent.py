import os, time
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE
from dotenv import load_dotenv
import logfire
from rich.console import Console

console = Console()

load_dotenv()

MODEL = os.getenv("MODEL")
MCP_SERVER_URL = "http://localhost:8000/sse"

logfire.configure(token=os.getenv("LOGFIRE_TOKEN"))
logfire.instrument_pydantic_ai()

server = MCPServerSSE(url=MCP_SERVER_URL)

# AWS agent
async def run_aws_agent(user_input):
    """Shared AWS agent function"""
    SYSTEM_PROMPT = (
        "You are a helpful assistant for AWS management.\n"
        "Use the right tools to answer user queries as accurately as possible.\n"
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
        mcp_servers=[server]
    )
    
    async with agent.run_mcp_servers():
        console.print("Running agent...")

        result = await agent.run(user_prompt)

        end_time = time.time()
        duration = end_time - start_time

        console.print(f"\n[bold green]✅ AGENT COMPLETED[/bold green]")
        console.print(f"Duration: {duration:.2f} seconds")

        return result