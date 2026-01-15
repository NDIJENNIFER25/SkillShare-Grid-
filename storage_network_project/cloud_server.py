from flask import Flask, request, jsonify
import time
from auth_utils import verify_node_credentials, generate_otp, print_otp

app = Flask(__name__)

# This stores information about all registered nodes
registered_nodes = {}

@app.route('/register', methods=['POST'])
def register_node():
    """Nodes call this to register - NOW WITH AUTHENTICATION"""
    data = request.json

    node_id = data.get('node_id')
    port = data.get('port')
    username = data.get('username')  # NEW: Require username
    password = data.get('password')  # NEW: Require password
    storage_capacity = data.get('storage_capacity', 15 * 1024 * 1024 * 1024)

    # Validate required fields
    if not all([node_id, port, username, password]):
        return jsonify({
            "error": "node_id, port, username, and password required"
        }), 400

    # Verify credentials
    print(f"🔐 Authentication attempt for node: {node_id} (username: {username})")
    is_valid, email = verify_node_credentials(username, password)

    if not is_valid:
        print(f"❌ Authentication failed for: {username}")
        return jsonify({
            "error": "Invalid credentials"
        }), 401

    print(f"✅ Credentials verified for: {username}")

    # Generate OTP for verification
    otp = generate_otp()
    print_otp(otp, email)

    # Register the node
    registered_nodes[node_id] = {
        'port': port,
        'ip': '127.0.0.1',
        'storage_capacity': storage_capacity,
        'last_seen': time.time(),
        'status': 'online',
        'username': username,
        'email': email,
        'otp_verified': True  # In production, this would be False until OTP is entered
    }

    print(f"✅ Node registered: {node_id} on port {port}")
    return jsonify({
        "status": "success",
        "message": f"Node {node_id} registered successfully",
        "otp_sent": True,
        "email": email
    }), 200

@app.route('/nodes', methods=['GET'])
def get_nodes():
    """Returns list of all registered nodes"""
    return jsonify({
        "nodes": registered_nodes,
        "total_nodes": len(registered_nodes)
    }), 200

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    """Nodes call this periodically to stay 'alive'"""
    data = request.json
    node_id = data.get('node_id')

    if node_id in registered_nodes:
        registered_nodes[node_id]['last_seen'] = time.time()
        registered_nodes[node_id]['status'] = 'online'
        return jsonify({"status": "success"}), 200

    return jsonify({"error": "Node not registered"}), 404

@app.route('/status', methods=['GET'])
def cloud_status():
    """Check if cloud is alive"""
    return jsonify({
        "status": "online",
        "total_nodes": len(registered_nodes),
        "uptime": "running",
        "security": "enabled"
    }), 200

if __name__ == '__main__':
    print("=" * 60)
    print("☁️  CLOUD SERVICE STARTING (WITH AUTHENTICATION)")
    print("=" * 60)
    print("📍 Running on: http://127.0.0.1:8000")
    print("🔐 Authentication: ENABLED")
    print("🎯 Nodes must provide username/password to register")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8000, debug=True)