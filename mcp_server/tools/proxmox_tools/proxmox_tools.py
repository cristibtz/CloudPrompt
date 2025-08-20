from proxmoxer import ProxmoxAPI
from dotenv import load_dotenv
import logging
import os

logger = logging.getLogger("proxmox_tools_mcp")

def register_tools(mcp):
    
    @mcp.tool()
    async def list_vms(
        node_name: str,
        proxmox_host: str = None,
        proxmox_user: str = None,
        proxmox_pass: str = None
    ):
        '''
        List all VMs on a Proxmox node or all nodes if no node is specified.
        :param node_name: Name of the Proxmox node to list VMs from. If not provided, lists VMs from all nodes.
        :param proxmox_host: Proxmox host address (optional, uses environment if not provided).
        :param proxmox_user: Proxmox username (optional, uses environment if not provided).
        :param proxmox_pass: Proxmox password (optional, uses environment if not provided).
        :return: List of VMs with their VMID, name, and status.
        :rtype: List[Dict[str, str]]
        :raises Exception: If there is an error connecting to Proxmox or listing VMs
        :return: List[Dict[str, str]] - List of VMs with their VMID, name, and status.
        '''
        
        print("Credentials:", proxmox_host, proxmox_user, proxmox_pass)

        # Ensure user has proper realm format for Proxmox
        user = proxmox_user or os.getenv('PROXMOX_USER')
        if user and '@' not in user:
            user = f"{user}@pam"

        proxmox = ProxmoxAPI(
            host=proxmox_host or os.getenv('PROXMOX_HOST'),
            user=user,
            password=proxmox_pass or os.getenv('PROXMOX_PASS'),
            verify_ssl=False
        )

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