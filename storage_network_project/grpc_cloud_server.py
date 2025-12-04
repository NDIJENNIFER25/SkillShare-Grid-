import grpc
from concurrent import futures
import time
import cloud_pb2
import cloud_pb2_grpc
from auth_utils_grpc import verify_credentials, create_otp, verify_otp, enroll_user

class CloudServiceServicer(cloud_pb2_grpc.CloudServiceServicer):
    def __init__(self):
        self.registered_nodes = {}

    def Register(self, request, context):
        """Register a node with authentication"""
        print(f"\n🔐 Registration attempt: {request.node_id} (user: {request.username})")

        # Verify credentials
        is_valid, email = verify_credentials(request.username, request.password)

        if not is_valid:
            print(f"❌ Authentication failed for: {request.username}")
            return cloud_pb2.RegisterResponse(
                success=False,
                message="Invalid credentials"
            )

        print(f"✅ Credentials verified for: {request.username}")

        # Generate OTP
        otp = create_otp(request.username, email)

        # Register node
        self.registered_nodes[request.node_id] = {
            'port': request.port,
            'username': request.username,
            'email': email,
            'storage_capacity': request.storage_capacity,
            'status': 'online',
            'last_seen': time.time()
        }

        print(f"✅ Node registered: {request.node_id} on port {request.port}")

        return cloud_pb2.RegisterResponse(
            success=True,
            message=f"Node {request.node_id} registered successfully",
            otp=otp,
            email=email
        )

    def Login(self, request, context):
        """User login"""
        print(f"\n🔑 Login attempt: {request.username}")

        is_valid, email = verify_credentials(request.username, request.password)

        if not is_valid:
            return cloud_pb2.LoginResponse(
                success=False,
                message="Invalid credentials"
            )

        otp = create_otp(request.username, email)

        return cloud_pb2.LoginResponse(
            success=True,
            message="Login successful",
            otp=otp,
            email=email
        )

    def Enroll(self, request, context):
        """Enroll new user"""
        print(f"\n📝 Enrollment request: {request.username}")

        success, message = enroll_user(request.username, request.email, request.password)

        return cloud_pb2.EnrollResponse(
            success=success,
            message=message
        )

    def VerifyOTP(self, request, context):
        """Verify OTP code"""
        is_valid, message = verify_otp(request.username, request.otp)

        return cloud_pb2.OTPResponse(
            verified=is_valid,
            message=message
        )

    def Heartbeat(self, request, context):
        """Node heartbeat"""
        if request.node_id in self.registered_nodes:
            self.registered_nodes[request.node_id]['last_seen'] = time.time()
            return cloud_pb2.HeartbeatResponse(alive=True)
        return cloud_pb2.HeartbeatResponse(alive=False)

    def GetNodes(self, request, context):
        """Get all registered nodes"""
        nodes = []
        for node_id, info in self.registered_nodes.items():
            nodes.append(cloud_pb2.Node(
                node_id=node_id,
                ip='127.0.0.1',
                port=info['port'],
                storage_capacity=info['storage_capacity'],
                status=info['status'],
                username=info['username']
            ))

        return cloud_pb2.NodesResponse(
            nodes=nodes,
            total_nodes=len(nodes)
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    cloud_pb2_grpc.add_CloudServiceServicer_to_server(CloudServiceServicer(), server)
    server.add_insecure_port('[::]:8000')

    print("=" * 60)
    print("☁️  gRPC CLOUD SERVER STARTING")
    print("=" * 60)
    print("📍 Running on: localhost:8000")
    print("🔐 Authentication: ENABLED")
    print("📧 OTP: ENABLED")
    print("👥 Enrollment: ENABLED")
    print("=" * 60)

    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()