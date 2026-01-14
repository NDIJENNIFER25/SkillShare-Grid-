import requests
import time

base = 'http://127.0.0.1:5000'
s = requests.Session()

username = 'e2e_test_user'
email = 'e2e_test@example.com'
password = 'Secret123'

print('1) Registering user...')
r = s.post(f'{base}/register', json={'username': username, 'email': email, 'password': password})
print('register:', r.status_code, r.text)
try:
    jr = r.json()
except Exception:
    jr = {}

if jr.get('status') == 'error' and 'exists' in jr.get('message',''):
    print('User already exists; continuing to login')

print('\n2) Logging in (requesting OTP)...')
r = s.post(f'{base}/login', json={'username': username, 'password': password})
print('login:', r.status_code, r.text)
lj = r.json()
otp = lj.get('otp')
if not otp:
    print('No OTP returned in login response; aborting')
    raise SystemExit(1)
print('Received OTP (for testing):', otp)

print('\n3) Verifying OTP...')
r = s.post(f'{base}/verify-otp', json={'otp': otp})
print('verify:', r.status_code, r.text)
vj = r.json()
user = vj.get('user')
if not user:
    print('Login verify did not return user info; aborting')
    raise SystemExit(1)
user_id = user.get('user_id')
print('Logged in user_id:', user_id)

print('\n4) Uploading a small file...')
files = {'file': ('hello.txt', b'Hello from e2e test')}
r = s.post(f'{base}/api/upload', files=files)
print('upload:', r.status_code, r.text)
ur = r.json()
file_id = ur.get('file_id')
if not file_id:
    print('Upload failed; aborting')
    raise SystemExit(1)
print('Uploaded file_id:', file_id)

print('\n5) Replicating file to node-eu-west...')
r = s.post(f'{base}/api/replicate/{file_id}', json={'target_node': 'node-eu-west'})
print('replicate:', r.status_code, r.text)

print('\n6) Check filesystem for replication...')
import os
vhd_path = os.path.join('vhd_storage', 'node-eu-west', user_id)
meta_path = os.path.join(vhd_path, '.metadata', f'{file_id}.json')
file_path = os.path.join(vhd_path, 'files', file_id)
print('expected vhd path:', vhd_path)
print('metadata exists:', os.path.exists(meta_path))
print('file exists:', os.path.exists(file_path))

print('\nE2E test complete.')
