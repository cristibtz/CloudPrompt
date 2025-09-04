from proxmoxer import ProxmoxAPI
from dotenv import load_dotenv
import logging
import os
from .auth_tools import get_proxmox_api

logger = logging.getLogger("proxmox_tools_mcp")

def register_tools(mcp):

    @mcp.tool()
    async def list_proxmox_nodes(
        session_id: str
    ):
        '''
        List all Proxmox nodes to help identify the correct node names.
        REQUIRES: authenticate_proxmox must be called first to establish a session.
        
        :param session_id: str - Proxmox session identifier from authenticate_proxmox.
        :return: List of available Proxmox nodes with their details.
        '''
        # Get authenticated Proxmox API
        proxmox = get_proxmox_api(session_id)
        if not proxmox:
            return {
                "error": f"No authenticated session found for '{session_id}'. Please call authenticate_proxmox first."
            }
        
        try:
            nodes = proxmox.nodes.get()
            logger.info(f"Found nodes: {nodes}")
            return {"nodes": nodes, "total_nodes": len(nodes)}
            
        except Exception as e:
            logger.error(f"Error listing nodes: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def list_vms(
        session_id: str,
        node_name: str = None
    ):
        '''
        List all VMs on a Proxmox node or all nodes if no node is specified.
        REQUIRES: authenticate_proxmox must be called first to establish a session.
        
        :param session_id: str - Proxmox session identifier from authenticate_proxmox.
        :param node_name: str - Name of the Proxmox node to list VMs from. If not provided, lists VMs from all nodes.
        :return: List of VMs with their VMID, name, and status.
        '''
        # Get authenticated Proxmox API
        proxmox = get_proxmox_api(session_id)
        if not proxmox:
            return {
                "error": f"No authenticated session found for '{session_id}'. Please call authenticate_proxmox first."
            }
        if not node_name:
            try:
                vms = []
                nodes = proxmox.nodes.get()
                logger.info(f"Found nodes: {nodes}")
                
                for node in nodes:
                    node_name_current = node["node"]
                    logger.info(f"Checking node: {node_name_current}")
                    try:
                        # Get QEMU VMs only
                        qemu_vms = proxmox.nodes(node_name_current).qemu.get()
                        
                        # Add QEMU VMs
                        for vm in qemu_vms:
                            vms.append({
                                "node": node_name_current,
                                "vmid": vm["vmid"],
                                "name": vm["name"],
                                "status": vm["status"]
                            })
                            
                    except Exception as node_error:
                        logger.error(f"Error listing VMs for node {node_name_current}: {node_error}")
                        vms.append({
                            "node": node_name_current,
                            "error": f"Could not list VMs: {str(node_error)}"
                        })
                return {"vms": vms, "total_nodes": len(nodes)}
            except Exception as e:
                logger.error(f"Error listing VMs: {e}")
                return {"error": str(e)}
        else:
            try:
                logger.info(f"Listing VMs for specific node: {node_name}")
                
                # Get QEMU VMs only
                qemu_vms = proxmox.nodes(node_name).qemu.get()
                
                logger.info(f"QEMU VMs from node {node_name}: {qemu_vms}")
                
                vms = []
                
                # Add QEMU VMs
                for vm in qemu_vms:
                    vms.append({
                        "node": node_name,
                        "vmid": vm["vmid"],
                        "name": vm["name"],
                        "status": vm["status"],
                        "cpu": vm.get("cpu", "N/A"),
                        "mem": vm.get("mem", "N/A"),
                        "maxmem": vm.get("maxmem", "N/A"),
                        "uptime": vm.get("uptime", "N/A")
                    })
                
                return {
                    "node": node_name, 
                    "vms": vms, 
                    "total_vms": len(vms)
                }
            except Exception as e:
                logger.error(f"Error listing VMs for node {node_name}: {e}")
                return {"error": f"Error listing VMs for node {node_name}: {str(e)}"}