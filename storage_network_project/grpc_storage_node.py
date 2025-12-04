import grpc
from concurrent import futures
import os
import sys
import time
import hashlib
import threading
import storage_pb2
import storage_pb2_grpc
import cloud_pb2
import cloud_pb2_grpc

class FileTransferServiceServicer(storage_pb2_grpc.FileTransferServiceServicer):
    def __init__(self, node_id, storage_capacity_gb=15):
        self.node_id = node_id
        self.storage_capacity = storage_capacity_gb * 1024 * 1024 * 1024
        self.used_storage = 0
        self.storage_path = os.path.join("node_storage", node_id)
        os.makedirs(self.storage_path, exist_ok=True)
        self.incoming_transfers = {}

    def PrepareReceive(self, request, context):
        """Prepare to receive a file"""
        # Check storage limit
        if self.used_storage + request.file_size > self.storage_capacity:
            print(f"❌ Insufficient storage! Used: {self.used_storage}, Needed: {request.file_size}")
            return storage_pb2.PrepareResponse(
                ready=False,
                message="Insufficient storage space"
            )

        self.incoming_transfers[request.file_id] = {
            'file_name': request.file_name,
            'file_size': request.file_size,
            'total_chunks': request.total_chunks,
            'received_chunks': {}
        }

        print(f"📥 Preparing to receive: {request.file_name} ({request.file_size} bytes)")

        return storage_pb2.PrepareResponse(
            ready=True,
            message="Ready to receive"
        )

    def TransferChunk(self, request, context):
        """Receive a file chunk"""
        if request.file_id not in self.incoming_transfers:
            return storage_pb2.ChunkResponse(
                success=False,
                ack=-1,
                node_id=self.node_id
            )

        # Verify checksum
        actual_checksum = hashlib.md5(request.chunk_data).hexdigest()
        if actual_checksum != request.checksum:
            print(f"❌ Checksum mismatch for chunk {request.chunk_id}")
            return storage_pb2.ChunkResponse(
                success=False,
                ack=-1,
                node_id=self.node_id
            )

        # Store chunk
        transfer = self.incoming_transfers[request.file_id]
        transfer['received_chunks'][request.chunk_id] = request.chunk_data

        print(f"📥 Received chunk {request.chunk_id + 1}/{transfer['total_chunks']}")

        # Check if all chunks received
        if len(transfer['received_chunks']) == transfer['total_chunks']:
            self._save_complete_file(request.file_id)

        return storage_pb2.ChunkResponse(
            success=True,
            ack=request.chunk_id,
            node_id=self.node_id
        )

    def GetStatus(self, request, context):
        """Get node status"""
        return storage_pb2.StatusResponse(
            node_id=self.node_id,
            status="online",
            storage_used=self.used_storage,
            storage_capacity=self.storage_capacity,
            storage_percent=(self.used_storage / self.storage_capacity) * 100
        )

    def _save_complete_file(self, file_id):
        """Save complete file from chunks"""
        transfer = self.incoming_transfers[file_id]
        file_name = transfer['file_name']
        final_path = os.path.join(self.storage_path, file_name)

        print(f"\n💾 Assembling complete file: {file_name}")

        with open(final_path, 'wb') as f:
            for chunk_id in sorted(transfer['received_chunks'].keys()):
                f.write(transfer['received_chunks'][chunk_id])

        self.used_storage += transfer['file_size']

        print(f"✅ File saved: {final_path}")
        print(f"📊 Storage used: {self.used_storage / (1024*1024):.2f} MB / {self.storage_capacity / (1024*1024*1024):.2f} GB")
        print(f"📊 Storage: {(self.used_storage/self.storage_capacity)*100:.2f}% full")

        del self.incoming_transfers[file_id]

class StorageNode:
    def __init__(self, node_id, port, username, password):
        self.node_id = node_id
        self.port = port
        self.username = username
        self.password = password
        self.cloud_url = 'localhost:8000'
        self.servicer = FileTransferServiceServicer(node_id)

    def register_with_cloud(self):
        """Register with cloud using gRPC"""
        try:
            with grpc.insecure_channel(self.cloud_url) as channel:
                stub = cloud_pb2_grpc.CloudServiceStub(channel)

                print(f"🔐 Authenticating with cloud...")
                response = stub.Register(cloud_pb2.RegisterRequest(
                    node_id=self.node_id,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    storage_capacity=self.servicer.storage_capacity
                ))

                if response.success:
                    print(f"✅ {response.message}")
                    print(f"📧 OTP sent to: {response.email}")
                    print(f"🔑 OTP: {response.otp}")
                    return True
                else:
                    print(f"❌ Registration failed: {response.message}")
                    return False
        except Exception as e:
            print(f"❌ Could not connect to cloud: {e}")
            return False

    def send_heartbeat(self):
        """Send periodic heartbeat"""
        while True:
            try:
                with grpc.insecure_channel(self.cloud_url) as channel:
                    stub = cloud_pb2_grpc.CloudServiceStub(channel)
                    stub.Heartbeat(cloud_pb2.HeartbeatRequest(node_id=self.node_id))
                    print(f"💓 Heartbeat sent")
            except:
                pass
            time.sleep(30)

    def start(self):
        """Start the node server"""
        print("=" * 60)
        print(f"🚀 Starting gRPC Storage Node: {self.node_id}")
        print("=" * 60)
        print(f"📍 Address: localhost:{self.port}")
        print(f"👤 Username: {self.username}")
        print(f"💾 Storage path: {self.servicer.storage_path}")
        print("=" * 60)

        if not self.register_with_cloud():
            print("❌ Failed to register with cloud")
            return

        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self.send_heartbeat, daemon=True)
        heartbeat_thread.start()

        # Start gRPC server
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        storage_pb2_grpc.add_FileTransferServiceServicer_to_server(self.servicer, server)
        server.add_insecure_port(f'[::]:{self.port}')
        server.start()

        print(f"✅ Node {self.node_id} running on port {self.port}")
        server.wait_for_termination()

if __name__ == '__main__':
    if len(sys.argv) != 5:
        print("Usage: python grpc_storage_node.py <node_id> <port> <username> <password>")
        print("Example: python grpc_storage_node.py node1 5001 node1 password123")
        sys.exit(1)

    node = StorageNode(sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4])
    node.start()