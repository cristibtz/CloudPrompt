import logging
import asyncio
import httpx
from fastmcp import FastMCP
from tools.aws_tools import register_aws_tools
from tools.azure_tools import register_azure_tools
from tools.gcp_tools import register_gcp_tools
from tools.proxmox_tools import register_proxmox_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cloudprompt_mcp")

http_client = httpx.AsyncClient(timeout=10.0)
mcp = FastMCP("CloudPrompt MCP Server",
                instructions = '''
                This is the MCP server for CloudPrompt, an AI agent that interacts with cloud providers.
                It provides tools to manage AWS, Azure, GCP, and Proxmox resources.
                Always ensure that the user is authenticated with the respective cloud provider before performing any operations.
                For AWS operations, the user MUST call 'authenticate_aws' first and use the returned session_id for subsequent operations.
                For Proxmox operations, the user MUST call 'authenticate_proxmox' first and use the returned session_id for subsequent operations.
                '''
)

register_aws_tools(mcp)
register_azure_tools(mcp)
register_gcp_tools(mcp)
register_proxmox_tools(mcp)

if __name__ == "__main__":
    try:
        logger.info("Starting MCP server on port 8000...")
        mcp.run(transport='streamable-http', port=8000)
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        asyncio.run(http_client.aclose())