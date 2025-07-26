import logging
import asyncio
import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP
from tools.aws_tools import register_aws_tools
from tools.azure_tools import register_azure_tools
from tools.gcp_tools import register_gcp_tools

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("aws_ec2_manager_mcp")

http_client = httpx.AsyncClient(timeout=10.0)
mcp = FastMCP("CloudPrompt MCP Server")

register_aws_tools(mcp)
register_azure_tools(mcp)
register_gcp_tools(mcp)

if __name__ == "__main__":
    try:
        logger.info("Starting MCP server on port 8000...")
        mcp.run(transport="sse")
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        asyncio.run(http_client.aclose())