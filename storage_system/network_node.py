"""
Network Node Communication System
Handles node discovery, communication, and file replication across network
"""
import socket
import json
import threading
import time
import requests
from typing import Dict, List, Optional
from pathlib import Path
import hashlib

class NetworkNode:
    """
    Represents a storage node in the distributed network
    Each node can communicate with other nodes via HTTP/TCP
    """

    def __init__(self, node_id: str, ip_address: str, port: int,
                 storage_path: str = "node_storage"):
        self.node_id = node_id
        self.ip_address = ip_address
        self.port = port
        self.storage_path = Path(storage_path) / node_id
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Node registry
        self.registry_file = self.storage_path / "node_registry.json"
        self.known_nodes = self._load_registry()

        # Node status
        self.status = "offline"
        self.is_running = False

        # Statistics
        self.stats = {
            "files_stored": 0,
            "total_size": 0,
            "files_replicated": 0,
            "requests_handled": 0,
            "uptime_start": None
        }

        # File index for this node
        self.file_index = {}
        self._load_file_index()

    def _load_registry(self) -> Dict:
        """Load known nodes from registry"""
        if self.registry_file.exists():
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_registry(self):
        """Save node registry"""
        with open(self.registry_file, 'w') as f:
            json.dump(self.known_nodes, f, indent=2)

    def _load_file_index(self):
        """Load file index for this node"""
        index_file = self.storage_path / "file_index.json"
        if index_file.exists():
            with open(index_file, 'r') as f:
                self.file_index = json.load(f)

    def _save_file_index(self):
        """Save file index"""
        index_file = self.storage_path / "file_index.json"
        with open(index_file, 'w') as f:
            json.dump(self.file_index, f, indent=2)

    def register_node(self, node_info: Dict) -> bool:
        """Register a new node in the network"""
        node_id = node_info['node_id']

        if node_id == self.node_id:
            print(f"Cannot register self")
            return False

        self.known_nodes[node_id] = {
            **node_info,
            "registered_at": time.time(),
            "last_seen": time.time(),
            "status": "active"
        }

        self._save_registry()
        print(f"[OK] Node registered: {node_id} at {node_info['ip_address']}:{node_info['port']}")
        return True

    def store_file(self, file_id: str, file_data: bytes,
                   file_metadata: Dict) -> bool:
        """Store a file on this node"""
        try:
            file_path = self.storage_path / f"{file_id}.bin"

            with open(file_path, 'wb') as f:
                f.write(file_data)

            self.file_index[file_id] = {
                **file_metadata,
                "stored_at": time.time(),
                "file_path": str(file_path),
                "size": len(file_data),
                "checksum": hashlib.sha256(file_data).hexdigest()
            }

            self._save_file_index()
            self.stats['files_stored'] += 1
            self.stats['total_size'] += len(file_data)

            print(f"[OK] File stored: {file_metadata.get('filename', file_id)} ({len(file_data)} bytes)")
            return True

        except Exception as e:
            print(f"✗ Error storing file: {e}")
            return False

    def retrieve_file(self, file_id: str) -> Optional[bytes]:
        """Retrieve a file from this node"""
        if file_id not in self.file_index:
            return None

        file_info = self.file_index[file_id]
        file_path = Path(file_info['file_path'])

        if not file_path.exists():
            return None

        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()

            checksum = hashlib.sha256(file_data).hexdigest()
            if checksum != file_info['checksum']:
                print(f"✗ File integrity check failed: {file_id}")
                return None

            return file_data

        except Exception as e:
            print(f"✗ Error retrieving file: {e}")
            return None

    def replicate_file_to_node(self, file_id: str, target_node_id: str) -> bool:
        """Replicate a file to another node"""
        if file_id not in self.file_index:
            print(f"✗ File not found: {file_id}")
            return False

        if target_node_id not in self.known_nodes:
            print(f"✗ Unknown node: {target_node_id}")
            return False

        file_data = self.retrieve_file(file_id)
        if not file_data:
            return False

        file_metadata = self.file_index[file_id]
        target_node = self.known_nodes[target_node_id]

        try:
            response = requests.post(
                f"http://{target_node['ip_address']}:{target_node['port']}/api/node/store",
                json={
                    "file_id": file_id,
                    "file_data": file_data.hex(),
                    "metadata": file_metadata
                },
                timeout=30
            )

            if response.status_code == 200:
                self.stats['files_replicated'] += 1
                print(f"[OK] File replicated to {target_node_id}: {file_metadata['filename']}")
                return True
            else:
                print(f"✗ Replication failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"✗ Error replicating file: {e}")
            return False

    def auto_replicate(self, file_id: str, replication_factor: int = 2) -> List[str]:
        """Automatically replicate a file to N other nodes"""
        active_nodes = [
            node_id for node_id, info in self.known_nodes.items()
            if info['status'] == 'active'
        ]

        if len(active_nodes) < replication_factor:
            print(f"⚠ Warning: Only {len(active_nodes)} active nodes available")
            replication_factor = len(active_nodes)

        replicated_to = []

        for i in range(replication_factor):
            if i < len(active_nodes):
                target_node_id = active_nodes[i]
                if self.replicate_file_to_node(file_id, target_node_id):
                    replicated_to.append(target_node_id)

        return replicated_to

    def get_node_info(self) -> Dict:
        """Get this node's information"""
        uptime = time.time() - self.stats['uptime_start'] if self.stats['uptime_start'] else 0

        return {
            "node_id": self.node_id,
            "ip_address": self.ip_address,
            "port": self.port,
            "status": self.status,
            "uptime_seconds": uptime,
            "statistics": self.stats,
            "storage_path": str(self.storage_path)
        }

    def start(self):
        """Start the node"""
        self.status = "active"
        self.is_running = True
        self.stats['uptime_start'] = time.time()
        print(f"[OK] Node started: {self.node_id} at {self.ip_address}:{self.port}")

    def stop(self):
        """Stop the node"""
        self.status = "offline"
        self.is_running = False
        print(f"[OK] Node stopped: {self.node_id}")


class NodeCluster:
    """Manages a cluster of nodes"""

    def __init__(self):
        self.nodes: Dict[str, NetworkNode] = {}
        self.primary_node_id = None

    def add_node(self, node: NetworkNode):
        """Add a node to the cluster"""
        self.nodes[node.node_id] = node

        if self.primary_node_id is None:
            self.primary_node_id = node.node_id

    def create_and_add_node(self, node_id: str, ip_address: str,
                           port: int) -> NetworkNode:
        """Create and add a new node"""
        node = NetworkNode(node_id, ip_address, port)
        self.add_node(node)
        return node

    def connect_nodes(self):
        """Connect all nodes to each other"""
        for node_id, node in self.nodes.items():
            for other_id, other_node in self.nodes.items():
                if node_id != other_id:
                    node.register_node({
                        "node_id": other_node.node_id,
                        "ip_address": other_node.ip_address,
                        "port": other_node.port
                    })

    def start_all_nodes(self):
        """Start all nodes in the cluster"""
        for node in self.nodes.values():
            node.start()

    def get_cluster_status(self) -> Dict:
        """Get status of entire cluster"""
        return {
            "total_nodes": len(self.nodes),
            "active_nodes": sum(1 for n in self.nodes.values() if n.status == 'active'),
            "primary_node": self.primary_node_id,
            "nodes": {
                node_id: node.get_node_info()
                for node_id, node in self.nodes.items()
            }
        }

    def store_file_with_replication(self, file_id: str, file_data: bytes,
                                   file_metadata: Dict,
                                   replication_factor: int = 2) -> Dict:
        """Store file on primary node and replicate to others"""
        if not self.primary_node_id or self.primary_node_id not in self.nodes:
            return {"error": "No primary node"}

        primary_node = self.nodes[self.primary_node_id]

        if not primary_node.store_file(file_id, file_data, file_metadata):
            return {"error": "Failed to store on primary node"}

        replicated_to = primary_node.auto_replicate(file_id, replication_factor)

        return {
            "success": True,
            "primary_node": self.primary_node_id,
            "replicated_to": replicated_to,
            "total_copies": len(replicated_to) + 1
        }