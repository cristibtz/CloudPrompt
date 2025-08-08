from proxmoxer import ProxmoxAPI

proxmox = ProxmoxAPI(
    "192.168.1.203", user="root@pam", password="26032004", verify_ssl=False
)

nodes = proxmox.nodes().get()[0]

vms = proxmox.nodes(nodes["node"]).qemu.get()

print(vms)

#for node in proxmox.nodes.get():
     #for vm in proxmox.nodes(node["node"]).qemu.get():
         #print(f"{vm['vmid']}. {vm['name']} => {vm['status']}")

