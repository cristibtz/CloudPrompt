import logging

logger = logging.getLogger("azure_hello_tools_mcp")

def register_tools(mcp):
    @mcp.tool()
    async def hello_azure(name: str):
        """
        A simple tool that returns a greeting message.
        :param name: str - Name of the person to greet.
        :return: str - Greeting message.
        """
        logger.info(f"Received request to greet {name}")
        greeting = f"Hello, {name}! Welcome to Azure tools."
        logger.info(f"Greeting generated: {greeting}")
        return greeting