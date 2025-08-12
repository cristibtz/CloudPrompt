from proxmoxer import ProxmoxAPI
from dotenv import load_dotenv
import logging
import os

proxmox = ProxmoxAPI(
    f'{os.getenv("PROXMOX_HOST")}', 
    user=f'{os.getenv("PROXMOX_USER")}@pam', 
    password=os.getenv("PROXMOX_PASS"), 
    verify_ssl=False
)

logger = logging.getLogger("proxmox_tools_mcp")


def register_tools(mcp):
    
    @mcp.tool()
    async def list_vms():
        try:
            vms = []
            for node in proxmox.nodes.get():
                for vm in proxmox.nodes(node["node"]).qemu.get():
                    vms.append({
                        "vmid": vm["vmid"],
                        "name": vm["name"],
                        "status": vm["status"]
                    })
            return vms
        except Exception as e:
            logger.error(f"Error listing VMs: {e}")
            return {"error": str(e)}
        