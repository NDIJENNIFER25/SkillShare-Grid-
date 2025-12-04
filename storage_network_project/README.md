# Distributed Cloud Storage Network with gRPC

## Features Implemented

### ✅ Core Requirements
- **5 Autonomous Storage Nodes** - Each with 15GB capacity
- **gRPC Communication** - Faster than HTTP/REST
- **Authentication System** - Bcrypt password hashing
- **OTP Verification** - Email-based two-factor authentication
- **Enrollment Service** - User registration via web and terminal
- **Storage Limit Enforcement** - 15GB per node strictly enforced
- **Calculator Service** - gRPC-based arithmetic operations

### ✅ Advanced Features
- **Web Dashboard** - Google Drive-like interface
- **Real-time Monitoring** - Live storage usage tracking
- **File Chunking** - 1MB chunks with TCP-style windowing
- **Checksum Verification** - MD5 checksums for data integrity
- **Heartbeat System** - Automatic node health monitoring

## Installation
```bash
pip install grpcio grpcio-tools bcrypt flask requests
```

## Generate gRPC Code
```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. storage.proto
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. calculator.proto
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. cloud.proto
```

## Setup Credentials
```bash
python setup_credentials.py
```

## Running the System

### 1. Start gRPC Cloud Server
```bash
python grpc_cloud_server.py
```

### 2. Start Calculator Service
```bash
python calculator_server.py
```

### 3. Start Storage Nodes
```bash
python grpc_storage_node.py node1 5001 node1 password123
python grpc_storage_node.py node2 5002 node2 password456
python grpc_storage_node.py node3 5003 node3 password789
python grpc_storage_node.py node4 5004 node4 password111
python grpc_storage_node.py node5 5005 node5 password222
```

### 4. Start Web Interface
```bash
python web_interface.py
```

Then open browser: http://localhost:5000

## Usage Examples

### Calculator (gRPC)
```bash
python calculator_client.py add 10 5
python calculator_client.py multiply 7 8
```

### File Transfer (gRPC)
```bash
python grpc_file_transfer.py test.txt 5002
```

### User Management
```bash
# Enroll new user
python cloud_client.py enroll username email@example.com password

# Login
python cloud_client.py login username password

# View all nodes
python cloud_client.py nodes
```

## Architecture
```
        ☁️ gRPC Cloud Server (Port 8000)
                    |
    ┌───────┬───────┼───────┬───────┐
    |       |       |       |       |
  Node1   Node2   Node3   Node4   Node5
  :5001   :5002   :5003   :5004   :5005
   15GB    15GB    15GB    15GB    15GB

  🧮 Calculator Service (Port 9000)
  🌐 Web Interface (Port 5000)
```

## Technologies Used

- **gRPC** - High-performance RPC framework
- **Protocol Buffers** - Efficient serialization
- **Flask** - Web interface backend
- **Bcrypt** - Password hashing
- **Threading** - Concurrent operations
- **HTML/CSS/JavaScript** - Web dashboard

## Project Structure
```
storage_network_project/
├── grpc_cloud_server.py       # gRPC cloud service
├── grpc_storage_node.py       # gRPC storage nodes
├── calculator_server.py       # Calculator service
├── calculator_client.py       # Calculator client
├── cloud_client.py            # Cloud management CLI
├── grpc_file_transfer.py      # File transfer client
├── web_interface.py           # Web dashboard backend
├── auth_utils_grpc.py         # Authentication utilities
├── email_utils.py             # OTP email utilities
├── storage.proto              # Storage service definition
├── calculator.proto           # Calculator service definition
├── cloud.proto                # Cloud service definition
├── credentials.txt            # User credentials (hashed)
├── templates/
│   └── index.html            # Web dashboard UI
└── node_storage/             # Node storage directories
    ├── node1/
    ├── node2/
    ├── node3/
    ├── node4/
    └── node5/
```

## Security Features

- ✅ Bcrypt password hashing (salt rounds: 12)
- ✅ OTP verification (6-digit codes)
- ✅ Credential validation on node registration
- ✅ Checksum verification for file transfers
- ✅ Storage quota enforcement

## Author

NDI JENNIFER

## Date

November 2024