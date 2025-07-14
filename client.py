import asyncio
import os, sys
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE
from dotenv import load_dotenv
import logfire

load_dotenv()

MODEL = os.getenv("MODEL")
MCP_SERVER_URL = "http://localhost:8000/sse"

logfire.configure(token='pylf_v1_eu_zfwsTtTCBXjKvVPnrrzPdx3Tz2CB1GYwr53trFtJ7NlB')
logfire.instrument_pydantic_ai()

server = MCPServerSSE(url=MCP_SERVER_URL)

async def main():
    user_input = sys.argv[1]

    user_prompt = f"{user_input}\n"
    user_prompt += "Always try to return a valid JSON format response without using without using '''json '''."

    print(user_prompt)
    if not user_prompt:
        print("Please provide a user prompt.")
        sys.exit(1)

    agent = Agent(
        name="Assistant",
        system_prompt="You are a helpful assistant for AWS EC2 management.",
        model=MODEL,
        mcp_servers=[server]
    )

    try: 
        async with agent.run_mcp_servers():
            result = await agent.run(user_prompt)
            print(result.output)
    except Exception as e:
        logger.error(f"Error in chat_with_agent: {str(e)}")
        return f"Error occurred: {str(e)}"

if __name__ == "__main__":
    asyncio.run(main())