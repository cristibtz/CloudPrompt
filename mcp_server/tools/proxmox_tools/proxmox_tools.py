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

    @mcp.tool()
    async def create_vm(
        session_id: str,
        node_name: str,
        name: str,
        cores: int,
        cpu: int,
        memory: int,
    ):
        pass
    @mcp.tool()
    async def start_vm(
        session_id: str,
        node_name: str,
        vmid: int
    ):
        '''
        Start a VM on a Proxmox node by its VMID.
        REQUIRES: authenticate_proxmox must be called first to establish a session.
        
        :param session_id: str - Proxmox session identifier from authenticate_proxmox.
        :param node_name: str - Name of the Proxmox node where the VM is located.
        :param vmid: int - VM ID to start.
        :return: Dict with operation status and VM information.
        '''
        # Get authenticated Proxmox API
        proxmox = get_proxmox_api(session_id)
        if not proxmox:
            return {
                "error": f"No authenticated session found for '{session_id}'. Please call authenticate_proxmox first."
            }
        
        try:
            logger.info(f"Starting VM {vmid} on node {node_name}")
            
            # Start the VM
            result = proxmox.nodes(node_name).qemu(vmid).status.start.post()
            
            # Get VM status after starting
            vm_status = proxmox.nodes(node_name).qemu(vmid).status.current.get()
            
            logger.info(f"Successfully started VM {vmid} on node {node_name}")
            
            return {
                "action": "start",
                "node": node_name,
                "vmid": vmid,
                "status": vm_status.get("status", "unknown"),
                "name": vm_status.get("name", "unknown"),
                "uptime": vm_status.get("uptime", 0),
                "info": f"VM {vmid} start command executed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error starting VM {vmid} on node {node_name}: {e}")
            return {"error": f"Failed to start VM {vmid} on node {node_name}: {str(e)}"}

    @mcp.tool()
    async def stop_vm(
        session_id: str,
        node_name: str,
        vmid: int
    ):
        '''
        Stop a VM on a Proxmox node by its VMID.
        REQUIRES: authenticate_proxmox must be called first to establish a session.
        
        :param session_id: str - Proxmox session identifier from authenticate_proxmox.
        :param node_name: str - Name of the Proxmox node where the VM is located.
        :param vmid: int - VM ID to stop.
        :return: Dict with operation status and VM information.
        '''
        # Get authenticated Proxmox API
        proxmox = get_proxmox_api(session_id)
        if not proxmox:
            return {
                "error": f"No authenticated session found for '{session_id}'. Please call authenticate_proxmox first."
            }
        
        try:
            logger.info(f"Stopping VM {vmid} on node {node_name}")
            
            # Stop the VM
            result = proxmox.nodes(node_name).qemu(vmid).status.stop.post()
            
            # Get VM status after stopping
            vm_status = proxmox.nodes(node_name).qemu(vmid).status.current.get()
            
            logger.info(f"Successfully stopped VM {vmid} on node {node_name}")
            
            return {
                "action": "stop",
                "node": node_name,
                "vmid": vmid,
                "status": vm_status.get("status", "unknown"),
                "name": vm_status.get("name", "unknown"),
                "info": f"VM {vmid} stop command executed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error stopping VM {vmid} on node {node_name}: {e}")
            return {"error": f"Failed to stop VM {vmid} on node {node_name}: {str(e)}"}

    @mcp.tool()
    async def list_iso_images(
        session_id: str,
        node_name: str = None
    ):
        '''
        List all ISO images available in Proxmox storage.
        REQUIRES: authenticate_proxmox must be called first to establish a session.
        
        :param session_id: str - Proxmox session identifier from authenticate_proxmox.
        :param node_name: str - Name of the Proxmox node to check storage. If not provided, checks all nodes.
        :return: Dict with list of ISO images and their details.
        '''
        # Get authenticated Proxmox API
        proxmox = get_proxmox_api(session_id)
        if not proxmox:
            return {
                "error": f"No authenticated session found for '{session_id}'. Please call authenticate_proxmox first."
            }
        
        try:
            iso_images = []
            
            if not node_name:
                # Get all nodes and check their storage
                nodes = proxmox.nodes.get()
                logger.info(f"Checking ISO images on all nodes: {[node['node'] for node in nodes]}")
                
                for node in nodes:
                    node_name_current = node["node"]
                    try:
                        # Get storage list for this node
                        storage_list = proxmox.nodes(node_name_current).storage.get()
                        
                        for storage in storage_list:
                            storage_id = storage["storage"]
                            storage_type = storage.get("type", "unknown")
                            
                            # Check if storage can contain ISOs
                            if storage.get("content", "").find("iso") != -1:
                                try:
                                    # Get ISO files from this storage
                                    storage_content = proxmox.nodes(node_name_current).storage(storage_id).content.get(content="iso")
                                    for item in storage_content:
                                        iso_images.append({
                                            "node": node_name_current,
                                            "storage": storage_id,
                                            "storage_type": storage_type,
                                            "volid": item["volid"],
                                            "format": item.get("format", "unknown"),
                                            "size": item.get("size", 0),
                                            "size_mb": round(item.get("size", 0) / (1024*1024), 2) if item.get("size") else 0,
                                            "filename": item["volid"].split("/")[-1] if "/" in item["volid"] else item["volid"]
                                        })
                                        
                                except Exception as storage_error:
                                    logger.warning(f"Could not access storage {storage_id} on node {node_name_current}: {storage_error}")
                                    
                    except Exception as node_error:
                        logger.error(f"Error checking storage on node {node_name_current}: {node_error}")
                        iso_images.append({
                            "node": node_name_current,
                            "error": f"Could not check storage: {str(node_error)}"
                        })
            else:
                # Check specific node
                logger.info(f"Checking ISO images on node: {node_name}")
                
                try:
                    # Get storage list for specified node
                    storage_list = proxmox.nodes(node_name).storage.get()
                    
                    for storage in storage_list:
                        storage_id = storage["storage"]
                        storage_type = storage.get("type", "unknown")
                        
                        # Check if storage can contain ISOs
                        if storage.get("content", "").find("iso") != -1:
                            try:
                                # Get ISO files from this storage
                                storage_content = proxmox.nodes(node_name).storage(storage_id).content.get(content="iso")
                                
                                for item in storage_content:
                                    iso_images.append({
                                        "node": node_name,
                                        "storage": storage_id,
                                        "storage_type": storage_type,
                                        "volid": item["volid"],
                                        "format": item.get("format", "unknown"),
                                        "size": item.get("size", 0),
                                        "size_mb": round(item.get("size", 0) / (1024*1024), 2) if item.get("size") else 0,
                                        "filename": item["volid"].split("/")[-1] if "/" in item["volid"] else item["volid"]
                                    })
                                    
                            except Exception as storage_error:
                                logger.warning(f"Could not access storage {storage_id} on node {node_name}: {storage_error}")
                                
                except Exception as e:
                    logger.error(f"Error checking storage on node {node_name}: {e}")
                    return {"error": f"Failed to check storage on node {node_name}: {str(e)}"}
            
            logger.info(f"Found {len(iso_images)} ISO images")
            
            return {
                "iso_images": iso_images,
                "total_images": len(iso_images),
                "node_filter": node_name if node_name else "all_nodes"
            }
            
        except Exception as e:
            logger.error(f"Error listing ISO images: {e}")
            return {"error": f"Failed to list ISO images: {str(e)}"}

    @mcp.tool()
    async def delete_vm(
        session_id: str,
        node_name: str,
        vmid: int
    ):
        '''
        Delete a VM on a Proxmox node by its VMID.
        REQUIRES: authenticate_proxmox must be called first to establish a session.

        :param session_id: str - Proxmox session identifier from authenticate_proxmox.
        :param node_name: str - Name of the Proxmox node where the VM is located.
        :param vmid: int - VM ID to delete.
        '''

        # Get authenticated Proxmox API
        proxmox = get_proxmox_api(session_id)
        if not proxmox:
            return {
                "error": f"No authenticated session found for '{session_id}'. Please call authenticate_proxmox first."
            }
        
        try:
            logger.info(f"Deleting VM {vmid} on node {node_name}")
            
            # First check if VM exists
            try:
                vm_config = proxmox.nodes(node_name).qemu(vmid).config.get()
                vm_name = vm_config.get('name', f'VM-{vmid}')
            except Exception:
                return {
                    "error": f"VM {vmid} not found on node {node_name}. It may have already been deleted or never existed."
                }
            
            # Delete the VM
            try:
                result = proxmox.nodes(node_name).qemu(vmid).delete()
                
                logger.info(f"Successfully deleted VM {vmid} ({vm_name}) on node {node_name}")

                return {
                    "action": "delete",
                    "node": node_name,
                    "vmid": vmid,
                    "vm_name": vm_name,
                    "task_id": result if result else "No task ID returned",
                    "info": f"VM {vmid} ({vm_name}) deletion initiated successfully"
                }
            except Exception as delete_error:
                return {
                    "error": f"Failed to delete VM {vmid} on node {node_name}: {str(delete_error)}"
                }
            
        except Exception as e:
            logger.error(f"Error deleting VM {vmid} on node {node_name}: {e}")
            