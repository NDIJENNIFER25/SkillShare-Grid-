from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from functools import wraps
import os
from simulation_controller import get_simulation
from auth_utils_grpc import verify_credentials, create_otp, verify_otp, enroll_user as enroll_user_func

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated', 'redirect': '/login'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user' in session:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard_page():
    if 'user' not in session:
        return redirect('/login')
    return render_template('dashboard.html', username=session['user'])

@app.route('/api/auth/enroll', methods=['POST'])
def enroll_user():
    data = request.json
    try:
        success, message = enroll_user_func(data['username'], data['email'], data['password'])
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/auth/login', methods=['POST'])
def login_user():
    data = request.json
    try:
        is_valid, email = verify_credentials(data['username'], data['password'])

        if is_valid:
            otp = create_otp(data['username'], email)
            session['pending_user'] = data['username']
            session['pending_otp'] = otp

            return jsonify({
                'success': True,
                'message': 'OTP sent to your email',
                'otp': otp,
                'email': email,
                'needs_otp': True
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/auth/verify-otp', methods=['POST'])
def verify_otp_route():
    data = request.json

    if 'pending_user' not in session:
        return jsonify({'success': False, 'message': 'No pending login'})

    if data['otp'] == session.get('pending_otp'):
        session['user'] = session['pending_user']
        session['authenticated'] = True
        session.pop('pending_user', None)
        session.pop('pending_otp', None)

        return jsonify({'success': True, 'message': 'Login successful', 'redirect': '/dashboard'})
    else:
        return jsonify({'success': False, 'message': 'Invalid OTP'})

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'redirect': '/login'})

@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    if 'user' in session:
        return jsonify({'authenticated': True, 'username': session['user']})
    return jsonify({'authenticated': False})

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})

    try:
        file.seek(0, 2)
        file_size_bytes = file.tell()
        file.seek(0)
        file_size_mb = file_size_bytes / (1024 * 1024)

        sim = get_simulation()
        cloudlet_id = sim.submit_file_transfer(int(file_size_mb) or 1)

        return jsonify({
            'success': True,
            'message': f'File {file.filename} submitted to simulation',
            'cloudlet_id': cloudlet_id,
            'file_size_mb': file_size_mb,
            'username': session['user']
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/simulation/vms', methods=['GET'])
@login_required
def get_simulation_vms():
    try:
        sim = get_simulation()
        return jsonify({'success': True, 'vms': sim.get_vm_status()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/simulation/queue', methods=['GET'])
@login_required
def get_simulation_queue():
    try:
        sim = get_simulation()
        return jsonify({'success': True, 'queue': sim.get_queue_status()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/simulation/completed', methods=['GET'])
@login_required
def get_simulation_completed():
    try:
        sim = get_simulation()
        return jsonify({'success': True, 'completed': sim.get_completed_tasks()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/simulation/stats', methods=['GET'])
@login_required
def get_simulation_stats():
    try:
        sim = get_simulation()
        return jsonify({'success': True, 'stats': sim.get_statistics()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("=" * 60)
    print("🌐 CLOUD SIMULATION WEB INTERFACE")
    print("=" * 60)
    print("📍 Login: http://localhost:5000/login")
    print("📍 Dashboard: http://localhost:5000/dashboard")
    print("🎮 Simulation running in background")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)