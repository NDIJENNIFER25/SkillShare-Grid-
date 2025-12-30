from flask import Flask, request, jsonify
import requests
import threading
import time
import os
import sys
import hashlib

class NetworkNode:
    def __init__(self, node_id, port, username, password, storage_capacity_gb=15):
        self.node_id = node_id
        self.port = port
        self.username = username
        self.password = password
        self.storage_capacity = storage_capacity_gb * 1024 * 1024 * 1024
        self.used_storage = 0
        self.cloud_url = "http://127.0.0.1:8000"

        # Create storage folder for this node
        self.storage_path = os.path.join("node_storage", node_id)
        os.makedirs(self.storage_path, exist_ok=True)

        # Track incoming file transfers
        self.incoming_transfers = {}

        # Flask app for this node
        self.app = Flask(f"node_{node_id}")
        self.setup_routes()

        print(f"📦 Node {node_id} initialized")
        print(f"👤 Username: {username}")
        print(f"💾 Storage path: {self.storage_path}")
        print(f"📊 Capacity: {storage_capacity_gb}GB")

    def setup_routes(self):
        """Setup Flask endpoints for this node"""

        @self.app.route('/status', methods=['GET'])
        def status():
            """Check if node is alive"""
            return jsonify({
                "node_id": self.node_id,
                "status": "online",
                "port": self.port,
                "username": self.username,
                "storage_used_bytes": self.used_storage,
                "storage_capacity_bytes": self.storage_capacity,
                "storage_used_percent": (self.used_storage / self.storage_capacity) * 100
            }), 200

        @self.app.route('/prepare_receive', methods=['POST'])
        def prepare_receive():
            """Prepare to receive a file"""
            data = request.json
            file_id = data.get('file_id')
            file_name = data.get('file_name')
            file_size = data.get('file_size')
            total_chunks = data.get('total_chunks')

            if self.used_storage + file_size > self.storage_capacity:
                return jsonify({"error": "Insufficient storage"}), 507

            self.incoming_transfers[file_id] = {
                'file_name': file_name,
                'file_size': file_size,
                'total_chunks': total_chunks,
                'received_chunks': {},
                'temp_path': os.path.join(self.storage_path, f"{file_id}.tmp")
            }

            print(f"📥 Preparing to receive: {file_name} ({file_size} bytes, {total_chunks} chunks)")

            return jsonify({"status": "ready"}), 200

        @self.app.route('/receive_chunk', methods=['POST'])
        def receive_chunk():
            """Receive a file chunk from another node"""
            data = request.json
            file_id = data.get('file_id')
            chunk_id = data.get('chunk_id')
            chunk_data_hex = data.get('chunk_data')
            checksum = data.get('checksum')

            if file_id not in self.incoming_transfers:
                return jsonify({"error": "File transfer not prepared"}), 400

            chunk_data = bytes.fromhex(chunk_data_hex)

            actual_checksum = hashlib.md5(chunk_data).hexdigest()
            if actual_checksum != checksum:
                return jsonify({"error": "Checksum mismatch"}), 400

            transfer = self.incoming_transfers[file_id]
            transfer['received_chunks'][chunk_id] = chunk_data

            print(f"📥 Received chunk {chunk_id + 1}/{transfer['total_chunks']}")

            if len(transfer['received_chunks']) == transfer['total_chunks']:
                self._save_complete_file(file_id)

            return jsonify({
                "status": "success",
                "ack": chunk_id,
                "node_id": self.node_id
            }), 200

    def _save_complete_file(self, file_id):
        """Save all received chunks as a complete file"""
        transfer = self.incoming_transfers[file_id]
        file_name = transfer['file_name']
        final_path = os.path.join(self.storage_path, file_name)

        print(f"\n💾 Assembling complete file: {file_name}")

        with open(final_path, 'wb') as f:
            for chunk_id in sorted(transfer['received_chunks'].keys()):
                f.write(transfer['received_chunks'][chunk_id])

        self.used_storage += transfer['file_size']

        print(f"✅ File saved: {final_path}")
        print(f"📊 Storage used: {self.used_storage / (1024*1024):.2f} MB")

        del self.incoming_transfers[file_id]

    def register_with_cloud(self):
        """Register this node with the cloud service - WITH AUTHENTICATION"""
        try:
            print(f"🔐 Authenticating with credentials...")
            response = requests.post(
                f"{self.cloud_url}/register",
                json={
                    "node_id": self.node_id,
                    "port": self.port,
                    "username": self.username,
                    "password": self.password,
                    "storage_capacity": self.storage_capacity
                },
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Successfully registered with cloud!")
                if data.get('otp_sent'):
                    print(f"📧 OTP sent to: {data.get('email')}")
                    print(f"🔑 Check console for OTP code")
                return True
            elif response.status_code == 401:
                print(f"❌ Authentication failed: Invalid credentials")
                return False
            else:
                print(f"❌ Failed to register: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Could not connect to cloud: {e}")
            return False

    def send_heartbeat(self):
        """Send periodic heartbeat to cloud to stay alive"""
        while True:
            try:
                requests.post(
                    f"{self.cloud_url}/heartbeat",
                    json={"node_id": self.node_id},
                    timeout=2
                )
                print(f"💓 Heartbeat sent")
            except Exception as e:
                print(f"⚠️  Heartbeat failed: {e}")

            time.sleep(30)

    def start(self):
        """Start the node server"""
        print("=" * 60)
        print(f"🚀 Starting Node: {self.node_id}")
        print("=" * 60)
        print(f"📍 Address: http://127.0.0.1:{self.port}")
        print(f"👤 Username: {self.username}")
        print(f"🔗 Registering with cloud at {self.cloud_url}")
        print("=" * 60)

        if self.register_with_cloud():
            heartbeat_thread = threading.Thread(target=self.send_heartbeat, daemon=True)
            heartbeat_thread.start()

            self.app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)
        else:
            print("❌ Failed to start - could not register with cloud")
            print("💡 Check your username and password")

if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("Usage: python network_node.py <node_id> <port> <username> <password>")
        print("Example: python network_node.py node1 5001 node1 password123")
        sys.exit(1)

    node_id = sys.argv[1]
    port = int(sys.argv[2])
    username = sys.argv[3]
    password = sys.argv[4]

    node = NetworkNode(node_id, port, username, password)

    node.start()

