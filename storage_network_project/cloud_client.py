import grpc
import sys
import cloud_pb2
import cloud_pb2_grpc

def enroll(username, email, password):
    """Enroll a new user"""
    with grpc.insecure_channel('localhost:8000') as channel:
        stub = cloud_pb2_grpc.CloudServiceStub(channel)
        response = stub.Enroll(cloud_pb2.EnrollRequest(
            username=username,
            email=email,
            password=password
        ))

        if response.success:
            print(f"✅ {response.message}")
        else:
            print(f"❌ {response.message}")

def login(username, password):
    """Login a user"""
    with grpc.insecure_channel('localhost:8000') as channel:
        stub = cloud_pb2_grpc.CloudServiceStub(channel)
        response = stub.Login(cloud_pb2.LoginRequest(
            username=username,
            password=password
        ))

        if response.success:
            print(f"✅ Login successful!")
            print(f"📧 OTP sent to: {response.email}")
            print(f"🔑 OTP: {response.otp}")
        else:
            print(f"❌ {response.message}")

def get_nodes():
    """Get all registered nodes"""
    with grpc.insecure_channel('localhost:8000') as channel:
        stub = cloud_pb2_grpc.CloudServiceStub(channel)
        response = stub.GetNodes(cloud_pb2.NodesRequest())

        print(f"\n📊 Total Nodes: {response.total_nodes}")
        print("=" * 60)

        for node in response.nodes:
            print(f"🖥️  Node: {node.node_id}")
            print(f"   👤 User: {node.username}")
            print(f"   📍 Address: {node.ip}:{node.port}")
            print(f"   💾 Capacity: {node.storage_capacity / (1024**3):.2f} GB")
            print(f"   📊 Status: {node.status}")
            print("-" * 60)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Enroll: python cloud_client.py enroll <username> <email> <password>")
        print("  Login:  python cloud_client.py login <username> <password>")
        print("  Nodes:  python cloud_client.py nodes")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'enroll' and len(sys.argv) == 5:
        enroll(sys.argv[2], sys.argv[3], sys.argv[4])
    elif command == 'login' and len(sys.argv) == 4:
        login(sys.argv[2], sys.argv[3])
    elif command == 'nodes':
        get_nodes()
    else:
        print("Invalid command or arguments")