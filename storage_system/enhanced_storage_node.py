import time
import json
from typing import Dict, List, Optional
from pathlib import Path
from .vhd_manager import VHDManager

class StorageNode:
    """Enhanced storage node with real file storage and networking"""

    def __init__(
        self,
        node_id: str,
        ip_address: str,
        storage_capacity_gb: int = 10,
        bandwidth_mbps: int = 1000
    ):
        self.node_id = node_id
        self.ip_address = ip_address
        self.storage_capacity_gb = storage_capacity_gb
        self.bandwidth_mbps = bandwidth_mbps

        # Initialize VHD Manager for this node
        vhd_base_path = Path("vhd_storage") / node_id
        self.vhd_manager = VHDManager(str(vhd_base_path))

        # Node status
        self.status = "online"
        self.connected_nodes: Dict[str, 'StorageNode'] = {}

        # Statistics
        self.total_requests = 0
        self.total_uploads = 0
        self.total_downloads = 0
        self.total_bytes_transferred = 0

        print(f"✅ Storage Node '{node_id}' initialized at {ip_address}")

    def connect_to_node(self, other_node: 'StorageNode'):
        """Connect this node to another node"""
        self.connected_nodes[other_node.node_id] = other_node
        other_node.connected_nodes[self.node_id] = self
        print(f"🔗 Node '{self.node_id}' connected to '{other_node.node_id}'")

    def create_user_storage(self, user_id: str, size_gb: int = 1) -> Dict:
        """Create storage space for a user"""
        result = self.vhd_manager.create_vhd(user_id, size_gb)
        if result['status'] == 'success':
            print(f"📦 Created {size_gb}GB storage for user '{user_id}' on node '{self.node_id}'")
        return result

    def upload_file(self, user_id: str, file_name: str, file_data: bytes) -> Dict:
        """Upload a file to user's storage"""
        # Simulate network transfer time
        transfer_time = len(file_data) / (self.bandwidth_mbps * 1024 * 1024 / 8)
        time.sleep(min(transfer_time, 0.1))  # Cap at 0.1s for demo

        result = self.vhd_manager.store_file(user_id, file_name, file_data)

        if result['status'] == 'success':
            self.total_uploads += 1
            self.total_bytes_transferred += len(file_data)
            print(f"⬆️  Uploaded '{file_name}' ({len(file_data)} bytes) for user '{user_id}'")

        self.total_requests += 1
        return result

    def download_file(self, user_id: str, file_id: str) -> Optional[Dict]:
        """Download a file from user's storage"""
        file_data = self.vhd_manager.retrieve_file(user_id, file_id)

        if file_data:
            # Simulate network transfer time
            transfer_time = len(file_data['file_data']) / (self.bandwidth_mbps * 1024 * 1024 / 8)
            time.sleep(min(transfer_time, 0.1))  # Cap at 0.1s for demo

            self.total_downloads += 1
            self.total_bytes_transferred += len(file_data['file_data'])
            print(f"⬇️  Downloaded '{file_data['metadata']['original_name']}' for user '{user_id}'")

        self.total_requests += 1
        return file_data

    def list_user_files(self, user_id: str) -> List[Dict]:
        """List all files for a user"""
        return self.vhd_manager.list_files(user_id)

    def delete_file(self, user_id: str, file_id: str) -> Dict:
        """Delete a file from user's storage"""
        result = self.vhd_manager.delete_file(user_id, file_id)
        if result['status'] == 'success':
            print(f"🗑️  Deleted file '{file_id}' for user '{user_id}'")
        return result

    def get_user_storage_info(self, user_id: str) -> Optional[Dict]:
        """Get storage usage info for a user"""
        return self.vhd_manager.get_storage_usage(user_id)

    def get_node_stats(self) -> Dict:
        """Get node statistics"""
        return {
            "node_id": self.node_id,
            "ip_address": self.ip_address,
            "status": self.status,
            "storage_capacity_gb": self.storage_capacity_gb,
            "bandwidth_mbps": self.bandwidth_mbps,
            "connected_nodes": list(self.connected_nodes.keys()),
            "total_requests": self.total_requests,
            "total_uploads": self.total_uploads,
            "total_downloads": self.total_downloads,
            "total_bytes_transferred": self.total_bytes_transferred,
            "total_mb_transferred": round(self.total_bytes_transferred / (1024 * 1024), 2)
        }

    def replicate_file_to_node(self, user_id: str, file_id: str, target_node_id: str) -> Dict:
        """Replicate a file to another connected node"""
        if target_node_id not in self.connected_nodes:
            return {
                "status": "error",
                "message": f"Node '{target_node_id}' not connected"
            }

        # Get file from this node
        file_data = self.download_file(user_id, file_id)
        if not file_data:
            return {
                "status": "error",
                "message": "File not found"
            }

        # Upload to target node
        target_node = self.connected_nodes[target_node_id]
        result = target_node.upload_file(
            user_id,
            file_data['metadata']['original_name'],
            file_data['file_data']
        )

        if result['status'] == 'success':
            print(f"🔄 Replicated file to node '{target_node_id}'")

        return result


class StorageNetwork:
    """Network of storage nodes"""

    def __init__(self, network_name: str = "CloudStorageNetwork"):
        self.network_name = network_name
        self.nodes: Dict[str, StorageNode] = {}
        print(f"🌐 Storage Network '{network_name}' initialized")

    def add_node(self, node: StorageNode):
        """Add a node to the network"""
        self.nodes[node.node_id] = node
        print(f"➕ Node '{node.node_id}' added to network")

    def remove_node(self, node_id: str):
        """Remove a node from the network"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            print(f"➖ Node '{node_id}' removed from network")

    def connect_nodes(self, node_id_1: str, node_id_2: str):
        """Connect two nodes in the network"""
        if node_id_1 in self.nodes and node_id_2 in self.nodes:
            self.nodes[node_id_1].connect_to_node(self.nodes[node_id_2])
            return True
        return False

    def get_node(self, node_id: str) -> Optional[StorageNode]:
        """Get a node by ID"""
        return self.nodes.get(node_id)

    def get_network_stats(self) -> Dict:
        """Get overall network statistics"""
        total_requests = sum(node.total_requests for node in self.nodes.values())
        total_uploads = sum(node.total_uploads for node in self.nodes.values())
        total_downloads = sum(node.total_downloads for node in self.nodes.values())
        total_bytes = sum(node.total_bytes_transferred for node in self.nodes.values())

        return {
            "network_name": self.network_name,
            "total_nodes": len(self.nodes),
            "nodes": [node.node_id for node in self.nodes.values()],
            "total_requests": total_requests,
            "total_uploads": total_uploads,
            "total_downloads": total_downloads,
            "total_mb_transferred": round(total_bytes / (1024 * 1024), 2)
        }

    def find_user_files(self, user_id: str) -> Dict[str, List[Dict]]:
        """Find all files for a user across all nodes"""
        user_files = {}
        for node_id, node in self.nodes.items():
            files = node.list_user_files(user_id)
            if files:
                user_files[node_id] = files
        return user_files