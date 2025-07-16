import os
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE
from dotenv import load_dotenv
import logfire

load_dotenv()

MODEL = os.getenv("MODEL")
MCP_SERVER_URL = "http://localhost:8000/sse"

logfire.configure(token=os.getenv("LOGFIRE_TOKEN"))
logfire.instrument_pydantic_ai()

server = MCPServerSSE(url=MCP_SERVER_URL)

async def run_aws_agent(user_input):
    """Shared AWS agent function"""
    SYSTEM_PROMPT = (
        "You are a helpful assistant for AWS management.\n"
        "Use the right tools to answer user queries as accurately as possible.\n"
    )

    user_prompt = f"{user_input}\n \
    Always try to return a valid JSON format response without using '''json '''.\n \
    Always return the result exactly the same from the MCP server, don't modify it unless explicitly asked.\n"
    
    agent = Agent(
        name="Assistant",
        system_prompt=SYSTEM_PROMPT,
        model=MODEL,
        mcp_servers=[server]
    )
    
    async with agent.run_mcp_servers():
        result = await agent.run(user_prompt)
        return result.output