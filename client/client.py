import asyncio
import os
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE
from dotenv import load_dotenv
import logfire
import streamlit as st

load_dotenv()

MODEL = os.getenv("MODEL")
MCP_SERVER_URL = "http://localhost:8000/sse"

logfire.configure(token=os.getenv("LOGFIRE_TOKEN"))
logfire.instrument_pydantic_ai()

server = MCPServerSSE(url=MCP_SERVER_URL)

async def run_aws_agent(user_input):
    SYSTEM_PROMPT = (
    "You are a helpful assistant for AWS EC2 management.\n"
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

def main():
    st.title("AWS EC2 Assistant")
    user_input = st.text_input("Enter your prompt:")
    if st.button("Submit") and user_input:
        with st.spinner("Processing..."):
            output = asyncio.run(run_aws_agent(user_input))
        st.markdown("### Response")
        st.code(output)

if __name__ == "__main__":
    main()