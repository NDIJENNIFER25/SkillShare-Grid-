from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_cors import CORS
import sys
import os
from pathlib import Path
import io
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth_system.user_manager import UserManager
from storage_system.enhanced_storage_node import StorageNode, StorageNetwork

# Get the directory where this file is located
current_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(current_dir, 'templates')
static_dir = os.path.join(current_dir, 'static')

# Create Flask app with explicit template folder
app = Flask(__name__,
            template_folder=template_dir,
            static_folder=static_dir)
app.secret_key = 'cloud-storage-secret-key-2024-change-this'
CORS(app)

# Initialize systems
print("\n" + "=" * 70)
print("[*] Initializing Cloud Storage System...")
print("=" * 70)

# Build email config from environment (safer than hard-coding credentials)
email_config = {
    "smtp_server": os.environ.get("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.environ.get("SMTP_PORT", "587")),
    "from_email": os.environ.get("SMTP_FROM_EMAIL", ""),
    "app_password": os.environ.get("SMTP_APP_PASSWORD", "")
}

user_manager = UserManager(email_config=email_config)
storage_network = StorageNetwork("ProductionCloudNetwork")

# Create multiple distributed storage nodes
print("\n[+] Creating distributed storage nodes...")
node1 = StorageNode("node-us-east", "192.168.1.10", storage_capacity_gb=50)
node2 = StorageNode("node-eu-west", "192.168.1.20", storage_capacity_gb=50)
node3 = StorageNode("node-asia", "192.168.1.30", storage_capacity_gb=50)

# Add nodes to network
storage_network.add_node(node1)
storage_network.add_node(node2)
storage_network.add_node(node3)

# Connect nodes to each other (mesh network)
print("\n[+] Connecting nodes in mesh network...")
storage_network.connect_nodes("node-us-east", "node-eu-west")
storage_network.connect_nodes("node-eu-west", "node-asia")
storage_network.connect_nodes("node-us-east", "node-asia")

# Use node1 as the main node for web interface
main_node = node1

print("[OK] System initialized successfully!")
print(f"[OK] Active nodes: {len(storage_network.nodes)}")
print(f"[OK] Network connections established")
print("=" * 70 + "\n")

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/')
def index():
    """Home page - redirect to login if not logged in"""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'GET':
        return render_template('register.html')

    # POST request - process registration
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # Register user
    result = user_manager.register_user(username, email, password)

    if result['status'] == 'success':
        # Create storage for user on main node
        storage_result = main_node.create_user_storage(result['user_id'], size_gb=5)

        return jsonify({
            'status': 'success',
            'message': 'Registration successful! You can now login.'
        })

    return jsonify(result), 400

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login - Step 1: Password"""
    if request.method == 'GET':
        return render_template('login.html')

    # POST request - process login
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # Authenticate and send OTP via email (requires SMTP config in env)
    result = user_manager.authenticate(username, password, send_email=True)

    if result['status'] == 'otp_required':
        # Store username in session for OTP verification
        session['pending_username'] = username
        return jsonify({
            'status': 'otp_required',
            'message': result['message'],
            'email': result['email']
        })

    return jsonify(result), 401

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    """User login - Step 2: OTP Verification"""
    data = request.json
    otp = data.get('otp')
    username = session.get('pending_username')

    if not username:
        return jsonify({
            'status': 'error',
            'message': 'Session expired. Please login again.'
        }), 401

    # Complete login with OTP
    result = user_manager.complete_login(username, otp)

    if result['status'] == 'success':
        # Set session
        session['username'] = username
        session['user_id'] = result['user']['user_id']
        session.pop('pending_username', None)

        return jsonify({
            'status': 'success',
            'message': 'Login successful!',
            'user': result['user']
        })

    return jsonify(result), 401

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('login'))

# ============================================================================
# DASHBOARD & FILE MANAGEMENT ROUTES
# ============================================================================

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'username' not in session:
        return redirect(url_for('login'))

    return render_template('dashboard.html', username=session['username'])

@app.route('/nodes')
def nodes_page():
    """Network nodes status page"""
    if 'username' not in session:
        return redirect(url_for('login'))

    # Get all nodes info
    nodes_info = []
    for node_id, node in storage_network.nodes.items():
        stats = node.get_node_stats()
        nodes_info.append(stats)

    # Get network stats
    network_stats = storage_network.get_network_stats()

    return render_template('nodes.html',
                         nodes=nodes_info,
                         network=network_stats,
                         username=session['username'])

@app.route('/upload-chunks')
def upload_chunks_page():
    """Chunked upload page"""
    if 'session_token' not in session:
        return redirect(url_for('login'))
    return render_template('upload_chunks.html')

@app.route('/api/files', methods=['GET'])
def list_files():
    """List user's files"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    user_id = session['user_id']
    files = main_node.list_user_files(user_id)

    return jsonify({
        'status': 'success',
        'files': files
    })

@app.route('/api/storage-info', methods=['GET'])
def storage_info():
    """Get user's storage information"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    user_id = session['user_id']
    usage = main_node.get_user_storage_info(user_id)

    if usage:
        return jsonify({
            'status': 'success',
            'storage': usage
        })

    return jsonify({'error': 'Storage info not found'}), 404

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload a file"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Read file data
    file_data = file.read()
    user_id = session['user_id']

    # Upload to storage
    result = main_node.upload_file(user_id, file.filename, file_data)

    if result['status'] == 'success':
        return jsonify({
            'status': 'success',
            'message': 'File uploaded successfully',
            'file_id': result['file_id']
        })

    return jsonify(result), 400

@app.route('/api/download/<file_id>', methods=['GET'])
def download_file(file_id):
    """Download a file"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    user_id = session['user_id']
    file_data = main_node.download_file(user_id, file_id)

    if file_data:
        return send_file(
            io.BytesIO(file_data['file_data']),
            as_attachment=True,
            download_name=file_data['metadata']['original_name']
        )

    return jsonify({'error': 'File not found'}), 404

@app.route('/api/delete/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Delete a file"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    user_id = session['user_id']
    result = main_node.delete_file(user_id, file_id)

    return jsonify(result)


@app.route('/api/replicate/<file_id>', methods=['POST'])
def replicate_file(file_id):
    """Replicate a file to another node"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.json or {}
    target_node_id = data.get('target_node')

    if not target_node_id:
        return jsonify({'error': 'Target node not specified'}), 400

    user_id = session['user_id']

    # Check if target node exists
    if target_node_id not in storage_network.nodes:
        return jsonify({'error': 'Target node not found'}), 404

    # Get the file from main node
    file_data = main_node.download_file(user_id, file_id)

    if not file_data:
        return jsonify({'error': 'File not found'}), 404

    # Get target node
    target_node = storage_network.nodes[target_node_id]

    # Create VHD on target node if it doesn't exist
    vhd_info = target_node.vhd_manager.get_vhd_info(user_id)
    if not vhd_info:
        target_node.create_user_storage(user_id, size_gb=1)

    # Upload file to target node
    result = target_node.upload_file(
        user_id,
        file_data['metadata']['original_name'],
        file_data['file_data']
    )

    if result.get('status') == 'success':
        return jsonify({
            'status': 'success',
            'message': f'File replicated to {target_node_id}',
            'target_node': target_node_id
        })

    return jsonify(result), 400

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("[*] Starting Flask Web Server...")
    print("=" * 70)
    print("[+] Server: http://127.0.0.1:5000")
    print("[+] Register: http://127.0.0.1:5000/register")
    print("[+] Login: http://127.0.0.1:5000/login")
    print("[+] Nodes: http://127.0.0.1:5000/nodes")
    print("=" * 70)
    print("\n[!] Press CTRL+C to stop the server\n")

    app.run(debug=True, host='0.0.0.0', port=5000)