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
    async def list_vms(
        node_name: str 
    ):
        '''
        List all VMs on a Proxmox node or all nodes if no node is specified.
        :param node_name: Name of the Proxmox node to list VMs from. If not provided, lists VMs from all nodes.
        :return: List[Dict[str, str]] - List of VMs with their VMID, name, and status.
        '''
        if not node_name:
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
        else:
            try:
                vms = [{"node_name": f"{node_name}"}]
                for vm in proxmox.nodes(node_name).qemu.get():
                    vms.append({
                        "vmid": vm["vmid"],
                        "name": vm["name"],
                        "status": vm["status"]
                    })
                return vms
            except Exception as e:
                logger.error(f"Error listing VMs for node {node_name}: {e}")
                return {"error": str(e)}