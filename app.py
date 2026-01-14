"""
Complete Flask Application
Integrates: VHD Storage, Network Nodes, Authentication, SkillShare, Admin Panel
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from pathlib import Path
import json
import os
import io
from datetime import datetime

# Import all our systems
from storage_system.vhd_manager import VHDManager
from storage_system.network_node import NetworkNode, NodeCluster
from storage_system.chunked_upload_handler import ChunkedUploadHandler
from storage_system.skillshare_manager import SkillShareManager
from auth_system.complete_auth import AuthenticationSystem

app = Flask(__name__, template_folder='web_interface/templates')
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB max file size

# Initialize all systems
print("Initializing Cloud Storage System...")
vhd_manager = VHDManager()
auth_system = AuthenticationSystem()
chunked_upload = ChunkedUploadHandler()
skillshare = SkillShareManager()

# Initialize node cluster with Cameroon regions
node_cluster = NodeCluster()
node_yaounde = node_cluster.create_and_add_node("node-yaounde", "192.168.1.10", 5000)
node_douala = node_cluster.create_and_add_node("node-douala", "192.168.1.20", 5001)
node_bafoussam = node_cluster.create_and_add_node("node-bafoussam", "192.168.1.30", 5002)
node_cluster.connect_nodes()
node_cluster.start_all_nodes()

print("[OK] All systems initialized")

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/')
def index():
    """Landing page"""
    if 'session_token' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login')
def login_page():
    """Login page"""
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    """Registration page"""
    if request.method == 'GET':
        return render_template('register.html')

    # Handle POST request
    data = request.json

    result = auth_system.register_user(
        email=data['email'],
        password=data['password'],
        full_name=data.get('username', data.get('full_name', 'User')),
        location=data.get('location', '')
    )

    if result['success']:
        # Create VHD for user
        user_vhd = vhd_manager.create_vhd(
            vhd_name=f"Storage_{result['user_id']}",
            size_gb=5,  # 5GB storage
            vhd_type="dynamic",
            user_id=result['user_id']
        )

        result['vhd_created'] = True
        result['vhd_id'] = user_vhd['vhd_id']

    return jsonify(result)

@app.route('/api/auth/verify-email', methods=['POST'])
def api_verify_email():
    """Verify email with OTP"""
    data = request.json
    result = auth_system.verify_email(data['email'], data['otp'])
    return jsonify(result)

@app.route('/api/auth/resend-otp', methods=['POST'])
def api_resend_otp():
    """Resend verification OTP"""
    data = request.json
    result = auth_system.resend_verification_otp(data['email'])
    return jsonify(result)

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Login user"""
    data = request.json
    result = auth_system.login(data['email'], data['password'])

    if result.get('success'):
        session['session_token'] = result['session_token']
        session['user_email'] = result['user']['email']
        session['user_id'] = result['user']['user_id']

    return jsonify(result)

@app.route('/api/auth/verify-2fa', methods=['POST'])
def api_verify_2fa():
    """Verify 2FA OTP"""
    data = request.json
    result = auth_system.verify_2fa(data['email'], data['otp'])

    if result.get('success'):
        session['session_token'] = result['session_token']
        session['user_email'] = result['user']['email']
        session['user_id'] = result['user']['user_id']

    return jsonify(result)

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """Logout user"""
    if 'session_token' in session:
        auth_system.logout(session['session_token'])
        session.clear()
    return jsonify({"success": True})

@app.route('/api/auth/enable-2fa', methods=['POST'])
def api_enable_2fa():
    """Enable 2FA"""
    if 'user_email' not in session:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    result = auth_system.enable_2fa(session['user_email'])
    return jsonify(result)

@app.route('/api/auth/disable-2fa', methods=['POST'])
def api_disable_2fa():
    """Disable 2FA"""
    if 'user_email' not in session:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    result = auth_system.disable_2fa(session['user_email'])
    return jsonify(result)

# ============================================================================
# USER DASHBOARD ROUTES
# ============================================================================

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'session_token' not in session:
        return redirect(url_for('login_page'))

    # Validate session
    user = auth_system.validate_session(session['session_token'])
    if not user:
        session.clear()
        return redirect(url_for('login_page'))

    return render_template('dashboard.html', user=user)

@app.route('/api/nodes', methods=['GET'])
def api_get_nodes():
    """Get cluster nodes status"""
    if 'session_token' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    cluster_status = node_cluster.get_cluster_status()
    return jsonify(cluster_status)

@app.route('/api/user/info', methods=['GET'])
def api_user_info():
    """Get current user info"""
    if 'session_token' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user = auth_system.validate_session(session['session_token'])
    if not user:
        return jsonify({"error": "Invalid session"}), 401

    # Get storage info
    storage = auth_system.get_storage_info(user['email'])

    return jsonify({
        "user_id": user['user_id'],
        "email": user['email'],
        "full_name": user['full_name'],
        "location": user.get('location', ''),
        "is_2fa_enabled": user['is_2fa_enabled'],
        "storage": storage,
        "member_since": datetime.fromtimestamp(user['created_at']).strftime('%Y-%m-%d')
    })

# ============================================================================
# FILE STORAGE ROUTES
# ============================================================================

@app.route('/api/files/upload', methods=['POST'])
def api_upload_file():
    """Upload a file"""
    if 'session_token' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user = auth_system.validate_session(session['session_token'])
    if not user:
        return jsonify({"error": "Invalid session"}), 401

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Read file data
    file_data = file.read()
    file_size = len(file_data)

    # Check storage quota
    storage = auth_system.get_storage_info(user['email'])
    if storage['free_bytes'] < file_size:
        return jsonify({"error": "Storage quota exceeded"}), 400

    # Get user's VHD
    user_vhds = vhd_manager.list_vhds(user_id=user['user_id'])
    if not user_vhds:
        # Create VHD if doesn't exist
        vhd = vhd_manager.create_vhd(
            vhd_name=f"Storage_{user['user_id']}",
            size_gb=1,
            vhd_type="dynamic",
            user_id=user['user_id']
        )
    else:
        vhd = user_vhds[0]

    # Store file in VHD
    try:
        filename = secure_filename(file.filename)
        file_path = f"/files/{filename}"

        file_metadata = vhd_manager.write_file_to_vhd(
            vhd_id=vhd['vhd_id'],
            file_path=file_path,
            file_data=file_data,
            user_id=user['user_id']
        )

        # Replicate to network nodes
        replication = node_cluster.store_file_with_replication(
            file_id=file_metadata['file_id'],
            file_data=file_data,
            file_metadata=file_metadata,
            replication_factor=1
        )

        # Update user storage usage
        new_usage = storage['used_bytes'] + file_size
        auth_system.update_storage_usage(user['email'], new_usage)

        return jsonify({
            "success": True,
            "file_id": file_metadata['file_id'],
            "filename": file_metadata['filename'],
            "size": file_metadata['size'],
            "replicated_to": replication.get('replicated_to', []),
            "message": "File uploaded successfully"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/files/list', methods=['GET'])
def api_list_files():
    """List user's files"""
    if 'session_token' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user = auth_system.validate_session(session['session_token'])
    if not user:
        return jsonify({"error": "Invalid session"}), 401

    # Get user's VHD
    user_vhds = vhd_manager.list_vhds(user_id=user['user_id'])
    if not user_vhds:
        return jsonify({"files": []})

    vhd = user_vhds[0]
    files = vhd_manager.list_files_in_vhd(vhd['vhd_id'], user_id=user['user_id'])

    return jsonify({
        "files": files,
        "count": len(files)
    })

@app.route('/api/files/download/<file_id>', methods=['GET'])
def api_download_file(file_id):
    """Download a file"""
    if 'session_token' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user = auth_system.validate_session(session['session_token'])
    if not user:
        return jsonify({"error": "Invalid session"}), 401

    # Get user's VHD
    user_vhds = vhd_manager.list_vhds(user_id=user['user_id'])
    if not user_vhds:
        return jsonify({"error": "No files found"}), 404

    vhd = user_vhds[0]

    try:
        # Read file from VHD
        file_data = vhd_manager.read_file_from_vhd(vhd['vhd_id'], file_id)

        # Get file metadata
        files = vhd_manager.list_files_in_vhd(vhd['vhd_id'])
        file_info = next((f for f in files if f['file_id'] == file_id), None)

        if not file_info:
            return jsonify({"error": "File not found"}), 404

        # Send file
        return send_file(
            io.BytesIO(file_data),
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=file_info['filename']
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/files/delete/<file_id>', methods=['DELETE'])
def api_delete_file(file_id):
    """Delete a file"""
    if 'session_token' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user = auth_system.validate_session(session['session_token'])
    if not user:
        return jsonify({"error": "Invalid session"}), 401

    # Get user's VHD
    user_vhds = vhd_manager.list_vhds(user_id=user['user_id'])
    if not user_vhds:
        return jsonify({"error": "No files found"}), 404

    vhd = user_vhds[0]

    # Get file info before deletion
    files = vhd_manager.list_files_in_vhd(vhd['vhd_id'])
    file_info = next((f for f in files if f['file_id'] == file_id), None)

    if not file_info:
        return jsonify({"error": "File not found"}), 404

    # Delete file
    success = vhd_manager.delete_file_from_vhd(vhd['vhd_id'], file_id)

    if success:
        # Update storage usage
        storage = auth_system.get_storage_info(user['email'])
        new_usage = storage['used_bytes'] - file_info['size']
        auth_system.update_storage_usage(user['email'], max(0, new_usage))

        return jsonify({
            "success": True,
            "message": "File deleted successfully"
        })
    else:
        return jsonify({"error": "Failed to delete file"}), 500

@app.route('/api/files/replicate/<file_id>', methods=['POST'])
def api_replicate_file(file_id):
    """Replicate file to other nodes"""
    if 'session_token' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user = auth_system.validate_session(session['session_token'])
    if not user:
        return jsonify({"error": "Invalid session"}), 401

    # Get user's VHD and find file
    user_vhds = vhd_manager.list_vhds(user_id=user['user_id'])
    if not user_vhds:
        return jsonify({"error": "No VHD found"}), 404

    vhd = user_vhds[0]
    files = vhd_manager.list_files_in_vhd(vhd['vhd_id'])
    file_info = next((f for f in files if f['file_id'] == file_id), None)

    if not file_info:
        return jsonify({"error": "File not found"}), 404

    # Read file data
    file_path = vhd_manager.get_file_path(vhd['vhd_id'], file_id, user['user_id'])
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
    except Exception as e:
        return jsonify({"error": f"Error reading file: {str(e)}"}), 500

    # Replicate to all nodes
    replication = node_cluster.store_file_with_replication(
        file_id=file_id,
        file_data=file_data,
        file_metadata=file_info,
        replication_factor=3
    )

    return jsonify(replication)

# ============================================================================
# SKILLSHARE ROUTES
# ============================================================================

@app.route('/skillshare')
def skillshare_page():
    """SkillShare Connect page"""
    if 'session_token' not in session:
        return redirect(url_for('login_page'))
    return render_template('skillshare.html')

@app.route('/api/skillshare/teachers', methods=['GET'])
def api_skillshare_teachers():
    """Get all teachers"""
    teachers = skillshare.get_all_teachers()
    return jsonify({"teachers": teachers})

@app.route('/api/skillshare/courses', methods=['GET'])
def api_skillshare_courses():
    """Get all courses"""
    courses = skillshare.get_all_courses()
    return jsonify({"courses": courses})

@app.route('/api/skillshare/stats', methods=['GET'])
def api_skillshare_stats():
    """Get SkillShare statistics"""
    stats = skillshare.get_statistics()
    return jsonify(stats)

@app.route('/api/skillshare/booking', methods=['POST'])
def api_skillshare_booking():
    """Create a booking"""
    if 'session_token' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user = auth_system.validate_session(session['session_token'])
    if not user:
        return jsonify({"error": "Invalid session"}), 401

    data = request.json
    booking = skillshare.create_booking(
        student_id=user['user_id'],
        teacher_id=data['teacher_id'],
        session_date=data['session_date'],
        session_time=data['session_time']
    )

    return jsonify(booking)

# ============================================================================
# ADMIN PANEL ROUTES
# ============================================================================

@app.route('/admin')
def admin_panel():
    """Admin panel"""
    if 'session_token' not in session:
        return redirect(url_for('login_page'))

    user = auth_system.validate_session(session['session_token'])
    if not user:
        return redirect(url_for('login_page'))

    # Check if user is admin (in production, add admin flag to user)
    # For now, first registered user is admin
    return render_template('admin.html', user=user)

@app.route('/api/admin/users', methods=['GET'])
def api_admin_users():
    """Get all users"""
    if 'session_token' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    users = auth_system.get_all_users()

    # Remove sensitive data
    safe_users = []
    for user in users:
        safe_users.append({
            "user_id": user['user_id'],
            "email": user['email'],
            "full_name": user['full_name'],
            "location": user.get('location', ''),
            "is_verified": user['is_verified'],
            "is_2fa_enabled": user['is_2fa_enabled'],
            "storage_quota_gb": user['storage_quota_gb'],
            "storage_used_bytes": user['storage_used_bytes'],
            "created_at": user['created_at'],
            "last_login": user.get('last_login'),
            "login_count": user.get('login_count', 0)
        })

    return jsonify({"users": safe_users, "count": len(safe_users)})

@app.route('/api/admin/nodes', methods=['GET'])
def api_admin_nodes():
    """Get all nodes"""
    if 'session_token' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    status = node_cluster.get_cluster_status()
    return jsonify(status)

@app.route('/api/admin/vhds', methods=['GET'])
def api_admin_vhds():
    """Get all VHDs"""
    if 'session_token' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    vhds = vhd_manager.list_vhds()
    return jsonify({"vhds": vhds, "count": len(vhds)})

@app.route('/api/admin/stats', methods=['GET'])
def api_admin_stats():
    """Get system statistics"""
    if 'session_token' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    users = auth_system.get_all_users()
    vhds = vhd_manager.list_vhds()
    cluster_status = node_cluster.get_cluster_status()

    total_storage_used = sum(u['storage_used_bytes'] for u in users)
    total_storage_allocated = sum(u['storage_quota_gb'] * 1024 * 1024 * 1024 for u in users)

    stats = {
        "total_users": len(users),
        "verified_users": sum(1 for u in users if u['is_verified']),
        "total_vhds": len(vhds),
        "total_nodes": cluster_status['total_nodes'],
        "active_nodes": cluster_status['active_nodes'],
        "total_storage_allocated_gb": total_storage_allocated / (1024 * 1024 * 1024),
        "total_storage_used_gb": total_storage_used / (1024 * 1024 * 1024),
        "storage_usage_percent": (total_storage_used / total_storage_allocated * 100) if total_storage_allocated > 0 else 0
    }

    return jsonify(stats)

# ============================================================================
# STORAGE NODE INFO ROUTES
# ============================================================================

@app.route('/api/storage/info', methods=['GET'])
def api_storage_info():
    """Get storage node information"""
    if 'session_token' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    status = node_cluster.get_cluster_status()

    nodes = []
    for node_id, node_info in status['nodes'].items():
        nodes.append({
            "id": node_id,
            "name": node_id.replace('-', ' ').title(),
            "ip_address": node_info['ip_address'],
            "port": node_info['port'],
            "status": node_info['status'],
            "files_stored": node_info['statistics']['files_stored'],
            "total_size": node_info['statistics']['total_size']
        })

    return jsonify({"nodes": nodes})

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("[CLOUD STORAGE SYSTEM]")
    print("="*60)
    print("\nFeatures:")
    print("  [+] VHD Storage System")
    print("  [+] Network Node Communication")
    print("  [+] Email Authentication with OTP")
    print("  [+] 2FA (Two-Factor Authentication)")
    print("  [+] File Upload/Download")
    print("  [+] SkillShare Connect")
    print("  [+] Admin Panel")
    print("  [+] 5GB Free Storage per User")
    print("\nStarting server...")
    print("="*60)

    app.run(debug=True, host='0.0.0.0', port=5000)