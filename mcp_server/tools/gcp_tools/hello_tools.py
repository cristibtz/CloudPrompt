import logging

logger = logging.getLogger("azure_gcp_tools_mcp")

def register_tools(mcp):
    @mcp.tool()
    async def hello_gcp(name: str):
        """
        A simple tool that returns a greeting message.
        :param name: str - Name of the person to greet.
        :return: str - Greeting message.
        """
        logger.info(f"Received request to greet {name}")
        greeting = f"Hello, {name}! Welcome to GCP tools."
        logger.info(f"Greeting generated: {greeting}")
        return greeting
    
    @mcp.tool()
    async def list_gcp_vms():
        """
        A tool that lists GCP virtual machines.
        :return: list - List of GCP VMs.
        """
        logger.info("Listing GCP virtual machines")
        # Simulate fetching VMs
        vms = ["vm1", "vm2", "vm3"]
        logger.info(f"Found VMs: {vms}")
        return vms